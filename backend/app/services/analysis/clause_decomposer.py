import re
from typing import List, Dict, Any


class ClauseDecomposer:
    """
    Descomponedor estructural de cláusulas jurídicas para contratos, convenios,
    demandas y documentos corporativos en la práctica jurídica mexicana.
    """

    # Patrones de encabezados de cláusulas y acápites estándar en México
    CLAUSE_HEADER_PATTERN = re.compile(
        r'(?:\n|^)\s*(?:(?:CL[AÁ]USULA\s+)?([A-ZÁÉÍÓÚÑ]{4,15}|(?:\d+[\.\-\)]))\s*[\.\:\-]\s*([^\n\r]+)?|\b(DECLARACIONES|ANTECEDENTES|PROEMIO|HECHOS|PRESTACIONES|DERECHO|PETITORIOS|TRANSITORIOS|RESOLUTIVOS)\b)',
        re.IGNORECASE
    )

    OBLIGATION_PATTERNS = [
        re.compile(r'(?:se\s+obliga\s+a|deber[áa]|pagar[áa]|entregar[áa]|asume\s+el\s+compromiso|se\s+compromete\s+a)\s+([^;\.\n]+)', re.IGNORECASE),
        re.compile(r'(?:queda\s+prohibido\s+a|no\s+podr[áa]|se\s+abstendr[áa]\s+de)\s+([^;\.\n]+)', re.IGNORECASE)
    ]

    RIGHT_PATTERNS = [
        re.compile(r'(?:tendr[áa]\s+derecho\s+a|podr[áa]|estar[áa]\s+facultad[oa]\s+para|se\s+reserva\s+el\s+derecho\s+de|gozar[áa]\s+de)\s+([^;\.\n]+)', re.IGNORECASE)
    ]

    DEADLINE_PATTERNS = [
        re.compile(r'(?:dentro\s+de\s+los|en\s+un\s+plazo\s+de|a\s+m[áa]s\s+tardar\s+en)\s*(\d+)\s*(d[íi]as(?:\s+h[áa]biles|\s+naturales)?|meses|a[ñn]os)', re.IGNORECASE),
        re.compile(r'(?:vigencia\s+(?:forzosa\s+)?de)\s*(\d+)\s*(d[íi]as|meses|a[ñn]os)', re.IGNORECASE)
    ]

    PENALTY_PATTERNS = [
        re.compile(r'(?:pena\s+convencional(?: equivalente al)?|inter[ée]s\s+moratorio(?: del)?|penalizaci[óo]n)\s*([^;\.\n]+)', re.IGNORECASE)
    ]

    @classmethod
    def decompose(cls, text: str) -> List[Dict[str, Any]]:
        """
        Segmenta el texto completo en cláusulas individuales y extrae metadatos analíticos.
        """
        if not text or not text.strip():
            return []

        # Buscar todos los encabezados
        matches = list(cls.CLAUSE_HEADER_PATTERN.finditer(text))
        
        # Si no se detectan encabezados estructurados, tratar el texto como cláusula única general
        if not matches:
            return [cls._build_clause_item(
                clause_num=1,
                title="Cláusula General / Contenido Íntegro",
                raw_text=text.strip()
            )]

        clauses = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            clause_block = text[start:end].strip()

            header_raw = match.group(0).strip()
            # Limpiar título
            title_text = re.sub(r'[\r\n]+', ' ', header_raw)
            if len(title_text) > 80:
                title_text = title_text[:77] + "..."

            clauses.append(cls._build_clause_item(
                clause_num=i + 1,
                title=title_text,
                raw_text=clause_block
            ))

        return clauses

    @classmethod
    def _build_clause_item(cls, clause_num: int, title: str, raw_text: str) -> Dict[str, Any]:
        """Genera el diccionario de la cláusula con obligaciones, derechos, plazos y penas."""
        # 1. Resumen ejecutivo de la cláusula (primera frase operativa sustantiva)
        sentences = [s.strip() for s in re.split(r'[\.\n]\s+', raw_text) if len(s.strip()) > 15]
        if sentences:
            summary = sentences[0] if len(sentences[0]) <= 220 else sentences[0][:217] + "..."
        else:
            summary = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text

        # 2. Obligaciones
        obligations = []
        for pat in cls.OBLIGATION_PATTERNS:
            for m in pat.finditer(raw_text):
                text_match = m.group(0).strip()
                if text_match not in obligations:
                    obligations.append(text_match)

        # 3. Derechos
        rights = []
        for pat in cls.RIGHT_PATTERNS:
            for m in pat.finditer(raw_text):
                text_match = m.group(0).strip()
                if text_match not in rights:
                    rights.append(text_match)

        # 4. Plazos
        deadlines = []
        for pat in cls.DEADLINE_PATTERNS:
            for m in pat.finditer(raw_text):
                text_match = m.group(0).strip()
                if text_match not in deadlines:
                    deadlines.append(text_match)

        # 5. Penalizaciones
        penalties = []
        for pat in cls.PENALTY_PATTERNS:
            for m in pat.finditer(raw_text):
                text_match = m.group(0).strip()
                if text_match not in penalties:
                    penalties.append(text_match)

        return {
            "clause_number": clause_num,
            "title": title,
            "raw_text": raw_text,
            "summary": summary,
            "obligations": obligations[:5],
            "rights": rights[:5],
            "deadlines": deadlines[:5],
            "penalties": penalties[:5]
        }
