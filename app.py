import os
import json
from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

INVOICE_FILE = 'invoice_number.json'

def get_next_invoice_number():
    if not os.path.exists(INVOICE_FILE):
        data = {'last_number': 1000}
        with open(INVOICE_FILE, 'w') as f:
            json.dump(data, f)
        return 1001
    
    with open(INVOICE_FILE, 'r') as f:
        data = json.load(f)
    
    next_number = data['last_number'] + 1
    data['last_number'] = next_number
    
    with open(INVOICE_FILE, 'w') as f:
        json.dump(data, f)
    
    return next_number

def create_pdf(company_info, products, logo_data=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, 
                           topMargin=2*cm, bottomMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    invoice_number = get_next_invoice_number()
    date_str = datetime.now().strftime('%d/%m/%Y')
    
    if logo_data:
        try:
            logo_buffer = BytesIO(logo_data)
            pil_img = PILImage.open(logo_buffer)
            
            aspect = pil_img.width / pil_img.height
            logo_height = 2*cm
            logo_width = logo_height * aspect
            
            logo = Image(logo_buffer, width=logo_width, height=logo_height)
            story.append(logo)
            story.append(Spacer(1, 0.5*cm))
        except:
            pass
    
    story.append(Paragraph("FATURA", title_style))
    story.append(Spacer(1, 0.3*cm))
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#34495e')
    )
    
    right_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    header_data = [
        [Paragraph(f"<b>{company_info['name']}</b><br/>{company_info['address']}<br/>"
                  f"Vergi Dairesi: {company_info['tax_office']}<br/>"
                  f"Vergi No: {company_info['tax_number']}<br/>"
                  f"Tel: {company_info['phone']}<br/>"
                  f"E-posta: {company_info['email']}", info_style),
         Paragraph(f"<b>Fatura No:</b> {invoice_number}<br/>"
                  f"<b>Tarih:</b> {date_str}", right_style)]
    ]
    
    header_table = Table(header_data, colWidths=[10*cm, 7*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 1*cm))
    
    table_data = [['Ürün/Hizmet', 'Miktar', 'Birim Fiyat', 'KDV %', 'Toplam']]
    
    subtotal = 0
    total_kdv = 0
    
    for product in products:
        qty = float(product['quantity'])
        price = float(product['price'])
        kdv_rate = float(product['kdv'])
        
        line_total = qty * price
        kdv_amount = line_total * (kdv_rate / 100)
        
        subtotal += line_total
        total_kdv += kdv_amount
        
        table_data.append([
            product['name'],
            str(qty),
            f"{price:.2f} ₺",
            f"%{kdv_rate}",
            f"{line_total:.2f} ₺"
        ])
    
    grand_total = subtotal + total_kdv
    
    products_table = Table(table_data, colWidths=[7*cm, 2*cm, 3*cm, 2*cm, 3*cm])
    products_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    story.append(products_table)
    story.append(Spacer(1, 1*cm))
    
    summary_data = [
        ['Ara Toplam:', f"{subtotal:.2f} ₺"],
        ['KDV Toplamı:', f"{total_kdv:.2f} ₺"],
        ['GENEL TOPLAM:', f"{grand_total:.2f} ₺"]
    ]
    
    summary_table = Table(summary_data, colWidths=[14*cm, 3*cm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 10),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#27ae60')),
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.HexColor('#27ae60')),
        ('TOPPADDING', (0, 2), (-1, 2), 10),
    ]))
    
    story.append(summary_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        company_info = {
            'name': request.form.get('company_name', ''),
            'address': request.form.get('company_address', ''),
            'tax_office': request.form.get('tax_office', ''),
            'tax_number': request.form.get('tax_number', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', '')
        }
        
        products_json = request.form.get('products', '[]')
        products = json.loads(products_json)
        
        if not products:
            return "En az bir ürün eklemelisiniz!", 400
        
        logo_data = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file.filename != '':
                logo_data = logo_file.read()
        
        pdf_buffer = create_pdf(company_info, products, logo_data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'fatura_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    
    except Exception as e:
        return f"Hata: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)