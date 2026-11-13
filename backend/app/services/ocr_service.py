import os
import platform
import subprocess
import tempfile
from typing import Tuple, Optional
import fitz
from app.core.logging import logger


class OCRService:
    """
    Servicio de Reconocimiento Óptico de Caracteres (OCR) Multiplataforma:
    - En Windows: Utiliza el motor nativo de hardware acelerado Windows.Media.Ocr.OcrEngine.
    - En Linux / Docker: Utiliza el motor Tesseract OCR (/usr/bin/tesseract).
    """

    @classmethod
    def is_ocr_available(cls) -> bool:
        """Determina si existe un motor de OCR ejecutable en el sistema operativo actual."""
        if platform.system() == "Windows":
            return True
        # En Linux comprobar si tesseract está en el PATH
        import shutil
        return shutil.which("tesseract") is not None

    @classmethod
    def extract_text_from_image(cls, image_path: str) -> str:
        """Extrae texto de un archivo de imagen (PNG, JPEG, TIFF)."""
        if not os.path.exists(image_path):
            logger.warning(f"[OCRService] Imagen no encontrada: {image_path}")
            return ""

        if platform.system() == "Windows":
            return cls._run_windows_native_ocr(image_path)
        else:
            return cls._run_tesseract_ocr(image_path)

    @classmethod
    def extract_text_from_scanned_pdf(cls, pdf_path: str, max_pages: int = 30) -> Tuple[str, int]:
        """
        Convierte páginas de PDF escaneado a imágenes temporales de alta resolución (150 DPI)
        y ejecuta OCR sobre cada página, agregando el texto procesado.
        """
        if not os.path.exists(pdf_path):
            return "", 0

        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        pages_to_process = min(total_pages, max_pages)
        extracted_pages = []

        logger.info(f"[OCRService] Iniciando procesamiento OCR para {pages_to_process} páginas de {pdf_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            for page_num in range(pages_to_process):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                temp_img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                pix.save(temp_img_path)

                page_text = cls.extract_text_from_image(temp_img_path)
                if page_text.strip():
                    extracted_pages.append(f"--- PÁGINA {page_num + 1} (OCR) ---\n\n{page_text}")
                else:
                    extracted_pages.append(f"--- PÁGINA {page_num + 1} (Sin texto detectable en OCR) ---")

        doc.close()
        full_text = "\n\n".join(extracted_pages)
        return full_text, total_pages

    @staticmethod
    def _run_windows_native_ocr(image_path: str) -> str:
        """Invoca el motor nativo de Windows (Windows.Media.Ocr.OcrEngine)."""
        clean_path = os.path.abspath(image_path)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        script_path = os.path.join(base_dir, "scripts", "windows_ocr.ps1")

        if not os.path.exists(script_path):
            logger.warning(f"[OCRService] Script no encontrado: {script_path}")
            return ""

        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, "-ImagePath", clean_path],
                capture_output=True,
                text=True,
                timeout=45,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0:
                return res.stdout.strip()
            else:
                logger.warning(f"[OCRService] Error en PowerShell OCR: {res.stderr[:200]}")
                return ""
        except Exception as e:
            logger.error(f"[OCRService] Excepción ejecutando OCR nativo en Windows: {e}")
            return ""

    @staticmethod
    def _run_tesseract_ocr(image_path: str) -> str:
        """Invoca Tesseract CLI en entornos Linux."""
        try:
            res = subprocess.run(
                ["tesseract", image_path, "stdout", "-l", "spa+eng"],
                capture_output=True,
                text=True,
                timeout=45,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0:
                return res.stdout.strip()
            else:
                logger.warning(f"[OCRService] Tesseract falló: {res.stderr[:200]}")
                return ""
        except Exception as e:
            logger.error(f"[OCRService] Excepción ejecutando Tesseract: {e}")
            return ""
