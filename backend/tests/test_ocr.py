import os
import tempfile
import pytest
from PIL import Image, ImageDraw
import fitz
from app.services.ocr_service import OCRService
from app.services.extraction_service import ExtractionService


def test_ocr_service_available():
    """Verifica que el servicio de OCR detecte un motor disponible en el entorno."""
    assert OCRService.is_ocr_available() is True


def test_ocr_extract_text_from_image():
    """Verifica el reconocimiento óptico de caracteres directo sobre un archivo de imagen."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img_path = tmp.name

    try:
        # Generar imagen sintética con texto jurídico
        img = Image.new("RGB", (900, 250), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((25, 40), "PODER NOTARIAL MERCANTIL PARA PLEITOS Y COBRANZAS", fill=(0, 0, 0))
        draw.text((25, 100), "LICENCIADO ALEJANDRO MORALES GARZA NOTARIO PUBLICO", fill=(0, 0, 0))
        draw.text((25, 160), "CIUDAD DE MEXICO A 10 DE ENERO DE 2026", fill=(0, 0, 0))
        img.save(img_path)

        extracted_text = OCRService.extract_text_from_image(img_path)
        assert len(extracted_text) > 10
        # Verificar palabras clave reconocidas
        clean = extracted_text.upper()
        assert any(k in clean for k in ["PODER", "NOTARIAL", "PLEITOS", "COBRANZAS", "MORALES", "MEXICO"])
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


def test_ocr_pipeline_integration_scanned_pdf():
    """Verifica la extracción automatizada con OCR en un PDF escaneado (baja densidad de texto)."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
        img_path = tmp_img.name
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name

    try:
        # 1. Crear imagen rasterizada
        img = Image.new("RGB", (1000, 250), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((30, 50), "CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES", fill=(0, 0, 0))
        draw.text((30, 110), "HONORARIOS MENSUALES POR VEINTE MIL PESOS", fill=(0, 0, 0))
        img.save(img_path)

        # 2. Insertar imagen en un PDF sin texto vectorial (simulando escáner de oficina)
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)
        page.insert_image(fitz.Rect(50, 50, 550, 200), filename=img_path)
        doc.save(pdf_path)
        doc.close()

        # 3. Procesar mediante el pipeline documental
        result = ExtractionService.process_document_pipeline(pdf_path, "application/pdf")
        assert result["ocr_applied"] is True
        assert result["page_count"] == 1
        safe_text_upper = result["safe_text"].upper()
        assert any(k in safe_text_upper for k in ["CONTRATO", "PRESTACION", "SERVICIOS", "PROFESIONALES", "HONORARIOS", "PESOS"])
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
