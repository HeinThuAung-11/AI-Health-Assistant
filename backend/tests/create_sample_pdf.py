
"""
Create a sample health report PDF for testing
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os


def create_sample_health_report():
    """Create a sample CBC (Complete Blood Count) report"""
    
    output_path = "tests/sample_health_report.pdf"
    
    # Create document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("<b>COMPLETE BLOOD COUNT (CBC)</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Patient info
    patient_info = Paragraph("""
        <b>Patient Name:</b> John Doe<br/>
        <b>Date of Birth:</b> 01/15/1985<br/>
        <b>Date Collected:</b> 10/10/2025<br/>
        <b>Report Date:</b> 10/11/2025
    """, styles['Normal'])
    elements.append(patient_info)
    elements.append(Spacer(1, 0.3*inch))
    
    # Results table
    data = [
        ['Test Name', 'Result', 'Unit', 'Reference Range', 'Status'],
        ['Hemoglobin', '13.2', 'g/dL', '13.5-17.5', 'Low'],
        ['White Blood Cells', '11.5', 'x10³/μL', '4.5-11.0', 'High'],
        ['Red Blood Cells', '4.8', 'M/μL', '4.5-5.5', 'Normal'],
        ['Platelets', '250', 'x10³/μL', '150-400', 'Normal'],
        ['Hematocrit', '40.5', '%', '38.8-50.0', 'Normal'],
        ['MCV', '88', 'fL', '80-100', 'Normal'],
    ]
    
    table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch, 1*inch])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Notes
    notes = Paragraph("""
        <b>Notes:</b><br/>
        - Hemoglobin is slightly below normal range<br/>
        - White blood cell count is slightly elevated<br/>
        - All other values are within normal limits<br/>
        - Recommend follow-up in 2 weeks
    """, styles['Normal'])
    elements.append(notes)
    
    # Build PDF
    doc.build(elements)
    
    print(f"✓ Sample PDF created: {output_path}")
    print(f"  File size: {os.path.getsize(output_path)} bytes")
    
    return output_path


if __name__ == "__main__":
    print("Creating sample health report PDF...\n")
    pdf_path = create_sample_health_report()
    print(f"\nYou can now test with: python tests/test_pdf_processor.py")
    print(f"Use this file path: {pdf_path}")
