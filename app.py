@app.route('/generate-pdf/<int:client_id>', methods=['POST'])
def generate_pdf(client_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    client = Client.query.get(client_id)
    service = request.form.get('service')
    amount = float(request.form.get('amount') or 0)
    gst_rate = float(request.form.get('gst_rate', 18))
    
    gst_amount = (amount * gst_rate) / 100
    total = amount + gst_amount

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # Header Style
    p.setFillColorRGB(0, 0.13, 0.29) # Navy Blue
    p.rect(0, 750, 600, 100, fill=1)
    
    p.setFillColorRGB(1, 1, 1) # White text
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(300, 800, "CA DEEPAK BHAYANA")
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 785, "Chartered Accountants | Paschim Vihar West Metro, Delhi - 110063")
    
    # Invoice Details
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 720, "TAX INVOICE")
    p.setFont("Helvetica", 10)
    p.drawRightString(550, 720, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    
    # Client Section
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(50, 710, 550, 710)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, 690, f"BILL TO:")
    p.setFont("Helvetica", 11)
    p.drawString(50, 675, f"{client.name}")
    p.setFont("Helvetica", 9)
    p.drawString(50, 660, f"GSTIN: {client.gstin if client.gstin else 'N/A'}")
    p.drawString(50, 645, f"Address: {client.address[:80] if client.address else 'N/A'}")
    
    # Table Header
    p.setFillColorRGB(0.95, 0.95, 0.95)
    p.rect(50, 600, 500, 20, fill=1)
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, 607, "Description of Service")
    p.drawRightString(540, 607, "Amount (INR)")
    
    # Table Content
    p.setFont("Helvetica", 10)
    p.drawString(60, 580, service)
    p.drawRightString(540, 580, f"{amount:,.2f}")
    
    # Totals Section
    p.line(350, 550, 550, 550)
    p.drawString(360, 530, "Taxable Value:")
    p.drawRightString(540, 530, f"{amount:,.2f}")
    p.drawString(360, 510, f"GST ({gst_rate}%):")
    p.drawRightString(540, 510, f"{gst_amount:,.2f}")
    
    p.setFillColorRGB(0, 0.13, 0.29)
    p.rect(350, 480, 200, 25, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(360, 487, "TOTAL PAYABLE:")
    p.drawRightString(540, 487, f"{total:,.2f}")
    
    # Footer
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 100, "This is a computer generated invoice and does not require a physical signature.")
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(550, 120, "For CA DEEPAK BHAYANA")
    p.drawRightString(550, 80, "Authorised Signatory")

    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Invoice_{client.name}.pdf", mimetype='application/pdf')
