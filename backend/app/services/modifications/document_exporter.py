import io
import re
from datetime import datetime, timezone
from typing import Optional

# DOCX Generation
from docx import Document as DocxDocument
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas de ReportLab de dos pasadas para calcular 'Página X de Y'."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Pie de página
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(letter[0] - 54, 36, page_str)
        self.drawString(54, 36, "Documento Procesado por LegalAI México • Validez Sujeta a Firma de Abogado")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, letter[0] - 54, 48)
        self.restoreState()


class DocumentExporter:
    """
    Exportador profesional de documentos jurídicos mexicanos a formatos DOCX y PDF.
    Cumple con tipografía legal, márgenes notariales e integridad criptográfica.
    """

    @classmethod
    def export_to_docx(
        cls,
        title: str,
        content_text: str,
        sha256_hash: Optional[str] = None,
        version_label: str = "Versión Definitiva",
        firm_name: str = "Bufete Jurídico México & Asociados"
    ) -> bytes:
        """Genera un archivo .docx profesional listo para edición en Microsoft Word."""
        doc = DocxDocument()

        # Configurar márgenes de página (2.5 cm en todos los bordes)
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # Encabezado institucional
        p_hdr = doc.add_paragraph()
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_hdr = p_hdr.add_run(f"{firm_name} | {version_label}")
        r_hdr.font.name = "Calibri"
        r_hdr.font.size = Pt(8.5)
        r_hdr.font.color.rgb = RGBColor(100, 116, 139)

        # Título del instrumento
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_before = Pt(12)
        p_title.paragraph_format.space_after = Pt(18)
        r_title = p_title.add_run(title.upper())
        r_title.bold = True
        r_title.font.name = "Calibri"
        r_title.font.size = Pt(14)
        r_title.font.color.rgb = RGBColor(15, 23, 42)

        # Metadatos de integridad
        if sha256_hash:
            p_meta = doc.add_paragraph()
            p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_meta = p_meta.add_run(f"Hash de Integridad Criptográfica SHA-256:\n{sha256_hash}")
            r_meta.font.name = "Consolas"
            r_meta.font.size = Pt(8)
            r_meta.font.color.rgb = RGBColor(71, 85, 105)
            p_meta.paragraph_format.space_after = Pt(18)

        # Separar en párrafos y cláusulas
        raw_paragraphs = [p.strip() for p in content_text.split("\n\n") if p.strip()]

        for para_str in raw_paragraphs:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(8)

            # Detectar encabezados de cláusula para formatear en negritas
            m = re.match(r'^((?:CL[AÁ]USULA\s+)?[A-ZÁÉÍÓÚÑ]{4,15}[\.\:\-]\s*[^:\.\n]+[\.\:])\s*(.*)$', para_str, re.IGNORECASE)
            if m:
                r_head = p.add_run(m.group(1) + " ")
                r_head.bold = True
                r_head.font.name = "Calibri"
                r_head.font.size = Pt(10.5)
                r_head.font.color.rgb = RGBColor(15, 23, 42)

                r_body = p.add_run(m.group(2))
                r_body.font.name = "Calibri"
                r_body.font.size = Pt(10.5)
                r_body.font.color.rgb = RGBColor(30, 41, 59)
            else:
                r_text = p.add_run(para_str)
                r_text.font.name = "Calibri"
                r_text.font.size = Pt(10.5)
                r_text.font.color.rgb = RGBColor(30, 41, 59)

        # Sección de firmas al pie
        doc.add_paragraph().paragraph_format.space_before = Pt(24)
        table = doc.add_table(rows=2, cols=2)
        table.alignment = WD_ALIGN_PARAGRAPH.CENTER

        cell_0 = table.cell(0, 0)
        cell_0.paragraphs[0].text = "_________________________________________\nPOR LA PRIMERA PARTE\n(Nombre y Firma de Representante)"
        cell_0.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        cell_1 = table.cell(0, 1)
        cell_1.paragraphs[0].text = "_________________________________________\nPOR LA SEGUNDA PARTE\n(Nombre y Firma de Representante)"
        cell_1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        out_stream = io.BytesIO()
        doc.save(out_stream)
        return out_stream.getvalue()

    @classmethod
    def export_to_pdf(
        cls,
        title: str,
        content_text: str,
        sha256_hash: Optional[str] = None,
        version_label: str = "Versión Definitiva",
        firm_name: str = "Bufete Jurídico México & Asociados"
    ) -> bytes:
        """Genera un archivo PDF legal de alta calidad con foliado y encabezados estructurados."""
        out_stream = io.BytesIO()
        pdf = SimpleDocTemplate(
            out_stream,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name='LegalTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            alignment=1,  # Center
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=12
        )

        meta_style = ParagraphStyle(
            name='LegalMeta',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=10,
            alignment=1,
            textColor=colors.HexColor('#475569'),
            spaceAfter=14
        )

        body_style = ParagraphStyle(
            name='LegalBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            alignment=4,  # Justify
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=8
        )

        story = []

        # Título
        story.append(Paragraph(title.upper(), title_style))

        # Metadatos de hash y versión
        if sha256_hash:
            meta_txt = f"<b>{firm_name}</b> • {version_label}<br/>SHA-256: {sha256_hash}"
            story.append(Paragraph(meta_txt, meta_style))

        story.append(Spacer(1, 10))

        # Párrafos del documento
        raw_paragraphs = [p.strip() for p in content_text.split("\n\n") if p.strip()]
        for para_str in raw_paragraphs:
            # Reemplazar saltos de línea internos por espacios
            clean_para = " ".join(para_str.split())
            
            # Formatear encabezados de cláusula
            m = re.match(r'^((?:CL[AÁ]USULA\s+)?[A-ZÁÉÍÓÚÑ]{4,15}[\.\:\-]\s*[^:\.\n]+[\.\:])\s*(.*)$', clean_para, re.IGNORECASE)
            if m:
                formatted_para = f"<b>{m.group(1)}</b> {m.group(2)}"
            else:
                formatted_para = clean_para

            story.append(Paragraph(formatted_para, body_style))

        story.append(Spacer(1, 24))

        # Bloque de Firmas
        sign_data = [
            [
                Paragraph("___________________________________<br/><b>POR LA PRIMERA PARTE</b><br/>Representante Legal", body_style),
                Paragraph("___________________________________<br/><b>POR LA SEGUNDA PARTE</b><br/>Representante Legal", body_style)
            ]
        ]
        t = Table(sign_data, colWidths=[240, 240])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)

        pdf.build(story, canvasmaker=NumberedCanvas)
        return out_stream.getvalue()
