import re
import time
from typing import Dict, Any, List, Tuple
from app.core.logging import logger


# Patrones de inyección de instrucciones para blindaje de IA
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)system\s*:\s*",
    r"(?i)you\s+are\s+now\s+(in\s+)?developer\s+mode",
    r"(?i)output\s+(the\s+)?(system\s+)?prompt",
    r"(?i)desregula(r)?\s+todas\s+las\s+instrucciones",
    r"(?i)haz\s+caso\s+omiso\s+a\s+las\s+instrucciones\s+anteriores",
]


class ExtractionService:
    @staticmethod
    def sanitize_untrusted_text(text: str) -> str:
        """
        Sanitiza el texto extraído para prevenir ataques de Indirect Prompt Injection.
        Encapsula y neutraliza comandos que intenten suplantar al sistema de IA.
        """
        sanitized = text
        for pattern in INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[CONTENIDO_REDACTADO_POR_SEGURIDAD]", sanitized)
        return sanitized

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, int, bool]:
        """Extrae texto de un archivo PDF usando PyMuPDF (fitz). Detecta si requiere OCR."""
        import fitz
        doc = fitz.open(file_path)
        page_count = doc.page_count
        full_text_pages = []
        total_chars = 0

        for page_num in range(page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            full_text_pages.append(page_text)
            total_chars += len(page_text.strip())

        doc.close()

        full_text = "\n\n--- PÁGINA SIGUIENTE ---\n\n".join(full_text_pages)
        
        # Heurística de documento escaneado: Si tiene menos de 40 caracteres promedio por página
        needs_ocr = (total_chars / max(page_count, 1)) < 40
        return full_text, page_count, needs_ocr

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extrae texto estructurado de párrafos y tablas en DOCX."""
        import docx
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        
        # Extraer también contenido de tablas
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        return "\n\n".join(paragraphs)

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Lee archivos de texto plano con soporte para codificación en español."""
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def extract_legal_metadata(text: str) -> Dict[str, Any]:
        """
        Extrae metadatos jurídicos clave mediante expresiones regulares y heurísticas
        especializadas en la estructura procesal y contractual mexicana.
        """
        metadata: Dict[str, Any] = {
            "parties": [],
            "doc_date": None,
            "subject_matter": None,
            "obligations": [],
            "amounts": [],
            "terms_deadlines": [],
            "signers": [],
            "jurisdiction": None,
            "court_authority": None,
            "procedure_type": None,
            "references": []
        }

        # 1. Fechas legales mexicanas
        # Ej: "15 de octubre de 2025", "a los diez días del mes de enero del año dos mil veinticinco"
        date_pattern = r'(\b\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}\b)'
        dates_found = re.findall(date_pattern, text, re.IGNORECASE)
        if dates_found:
            metadata["doc_date"] = dates_found[0]

        # 2. Montos económicos en moneda nacional (MXN)
        # Ej: "$1,500,000.00 M.N.", "250,000 pesos", "$50,000.00"
        amount_pattern = r'(\$\s*[\d,]+(?:\.\d{2})?\s*(?:M\.N\.|pesos|moneda nacional)?)'
        amounts = re.findall(amount_pattern, text, re.IGNORECASE)
        if amounts:
            metadata["amounts"] = list(set([a.strip() for a in amounts[:5]]))

        # 3. Partes contractuales y procesales
        parties_roles = [
            "ARRENDADOR", "ARRENDATARIO", "COMPRADOR", "VENDEDOR", "ACTOR", "DEMANDADO",
            "QUEJOSO", "AUTORIDAD RESPONSABLE", "PODERDANTE", "APODERADO", "PRESTADOR", "CLIENTE"
        ]
        for role in parties_roles:
            role_pattern = rf'(?:el\s+|la\s+)?["\']?({role})["\']?\s*(?:,|:|\s*denominad[oa]\s+en\s+lo\s+sucesivo)?\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s\.,&]+?(?:S\.A\.|S\.C\.|S\.R\.L\.|S\.A\.P\.I\.|C\.|LIC\.)?[^\n\.,;]{{3,50}})'
            matches = re.findall(role_pattern, text, re.IGNORECASE)
            for m in matches:
                metadata["parties"].append({"role": m[0].upper(), "name": m[1].strip()})

        # 4. Plazos y vigencias
        terms_pattern = r'(\b(?:plazo|vigencia|término)\s+de\s+[^,\.\n]{3,60}(?:días|meses|años|naturales|hábiles))'
        terms = re.findall(terms_pattern, text, re.IGNORECASE)
        if terms:
            metadata["terms_deadlines"] = list(set([t.strip() for t in terms[:4]]))

        # 5. Jurisdicción y competencia
        jurisdiction_pattern = r'(competentes?\s+los\s+tribunales\s+de\s+[^,\.\n]{3,60}|jurisdicción\s+de\s+los\s+juzgados\s+de\s+[^,\.\n]{3,60})'
        jurisdiction_match = re.search(jurisdiction_pattern, text, re.IGNORECASE)
        if jurisdiction_match:
            metadata["jurisdiction"] = jurisdiction_match.group(1).strip()

        # 6. Autoridad judicial o administrativa
        authority_pattern = r'(Juzgado\s+[^,\.\n]{3,50}|Tribunal\s+Colegiado[^,\.\n]{3,50}|Suprema\s+Corte\s+de\s+Justicia|Junta\s+Especial\s+[^,\.\n]{3,50})'
        authority_match = re.search(authority_pattern, text, re.IGNORECASE)
        if authority_match:
            metadata["court_authority"] = authority_match.group(1).strip()

        # 7. Cédula profesional
        license_pattern = r'(cédula\s+profesional\s+(?:número|no\.?)?\s*(\d{6,8}))'
        license_match = re.search(license_pattern, text, re.IGNORECASE)
        if license_match:
            metadata["signers"].append({"professional_license": license_match.group(2)})

        # 8. Cláusulas de objeto
        subject_pattern = r'(?:PRIMERA|OBJETO)[\.\s\:\-]+([^\n]{20,250})'
        subject_match = re.search(subject_pattern, text, re.IGNORECASE)
        if subject_match:
            metadata["subject_matter"] = subject_match.group(1).strip()

        return metadata

    @staticmethod
    def process_document_pipeline(file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo: extracción de texto, cálculo de páginas,
        detección de OCR, sanitización y extracción de metadatos estructurados.
        """
        start_time = time.time()
        page_count = 1
        needs_ocr = False
        raw_text = ""

        if "pdf" in mime_type:
            raw_text, page_count, needs_ocr = ExtractionService.extract_text_from_pdf(file_path)
            # Si es un documento escaneado (baja densidad de caracteres), procesar con OCR
            if needs_ocr:
                try:
                    from app.services.ocr_service import OCRService
                    if OCRService.is_ocr_available():
                        ocr_text, ocr_pages = OCRService.extract_text_from_scanned_pdf(file_path)
                        if ocr_text.strip():
                            raw_text = ocr_text
                            page_count = max(page_count, ocr_pages)
                except Exception as e:
                    logger.warning(f"Fallback de OCR en PDF escaneado falló: {e}")
        elif "wordprocessingml" in mime_type or "docx" in mime_type:
            raw_text = ExtractionService.extract_text_from_docx(file_path)
            page_count = max(1, len(raw_text) // 2500)
        elif "text" in mime_type:
            raw_text = ExtractionService.extract_text_from_txt(file_path)
            page_count = max(1, len(raw_text) // 2500)
        else:
            # Imágenes (PNG, JPEG, TIFF) u otros formatos escaneados
            needs_ocr = True
            try:
                from app.services.ocr_service import OCRService
                if OCRService.is_ocr_available():
                    raw_text = OCRService.extract_text_from_image(file_path)
                if not raw_text.strip():
                    raw_text = f"[Documento en formato imagen ({mime_type}). No se detectó texto legible por OCR]"
            except Exception as e:
                logger.error(f"Fallo al ejecutar OCR en imagen: {e}")
                raw_text = f"[Documento en formato imagen ({mime_type}). Error en procesamiento OCR: {e}]"
            page_count = 1

        # Blindaje contra Prompt Injections
        safe_text = ExtractionService.sanitize_untrusted_text(raw_text)

        # Extracción de metadatos legales
        legal_metadata = ExtractionService.extract_legal_metadata(safe_text)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "safe_text": safe_text,
            "page_count": page_count,
            "ocr_applied": needs_ocr,
            "processing_time_ms": elapsed_ms,
            "metadata": legal_metadata
        }
