from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os

# Register Arabic font
FONT_PATH = "arial.ttf"  # You'll need to provide the path to an Arabic-compatible font
pdfmetrics.registerFont(TTFont('Arabic', FONT_PATH))

def create_pdf(markdown_file, output_pdf):
    # Create PDF document
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    arabic_style = ParagraphStyle(
        'Arabic',
        fontName='Arabic',
        fontSize=16,
        rightIndent=0,
        leftIndent=0,
        alignment=2  # Right alignment for Arabic
    )
    
    trans_style = ParagraphStyle(
        'Translation',
        fontSize=12,
        rightIndent=0,
        leftIndent=0,
        alignment=0  # Left alignment for transliteration
    )

    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Process content
    story = []
    
    # Add title
    title = Paragraph("Dua Qunoot with Transliteration", title_style)
    story.append(title)
    story.append(Spacer(1, 20))

    # Process table content
    table_data = []
    is_table = False
    
    for line in lines:
        if '|' in line and '-|-' not in line:
            if not is_table:
                is_table = True
                continue  # Skip the header row
            
            # Split the line into columns
            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) == 2:
                arabic = Paragraph(cols[0], arabic_style)
                trans = Paragraph(cols[1], trans_style)
                table_data.append([arabic, trans])

    # Create table
    if table_data:
        table = Table(table_data, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ]))
        story.append(table)

    # Build PDF
    doc.build(story)

if __name__ == "__main__":
    input_file = "dua_qunoot.md"
    output_file = "dua_qunoot.pdf"
    
    if not os.path.exists(FONT_PATH):
        print(f"Please download an Arabic-compatible font (like Arial) and update the FONT_PATH variable")
    else:
        create_pdf(input_file, output_file)
        print(f"PDF has been created successfully: {output_file}") 