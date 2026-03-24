import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.pdfgen import canvas
from datetime import datetime
import io

# Render ke liye path settings
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'billing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. Database Model for Clients
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(15))
    email = db.Column(db.String(100))

# --- ISSE DATABASE TABLE BAN JAYEGI ---
with app.app_context():
    db.create_all()

# 2. Home Page (Dashboard)
@app.route('/')
def index():
    try:
        all_clients = Client.query.all()
        return render_template('index.html', clients=all_clients)
    except Exception as e:
        # Agar table nahi milti toh ye error dikhayega
        return f"Database Error: {str(e)}. Please refresh or wait a minute."

# 3. Naya Client Add Karne Ka Route
@app.route('/add-client', methods=['POST'])
def add_client():
    name = request.form.get('name')
    gstin = request.form.get('gstin')
    email = request.form.get('email')
    
    if name:
        new_client = Client(name=name, gstin=gstin, email=email)
        db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('index'))

# 4. Bill Form Dikhaane Ka Route
@app.route('/create-bill/<int:client_id>')
def create_bill(client_id):
    client = Client.query.get(client_id)
    return render_template('create_bill.html', client=client)

# 5. PDF Generate Ka Route
@app.route('/generate-pdf/<int:client_id>', methods=['POST'])
def generate_pdf(client_id):
    client = Client.query.get(client_id)
    service = request.form.get('service')
    amount_str = request.form.get('amount')
    amount = float(amount_str) if amount_str else 0.0
    gst_rate = float(request.form.get('gst_rate', 18))

    gst_amount = (amount * gst_rate) / 100
    total = amount + gst_amount

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(300, 800, "CA DEEPAK BHAYANA")
    p.setFont("Helvetica", 12)
    p.drawCentredString(300, 780, "Chartered Accountants | Tax Consultant")
    p.line(50, 765, 550, 765)

    # Info
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 740, f"INVOICE TO:")
    p.setFont("Helvetica", 12)
    p.drawString(50, 725, f"Client Name: {client.name}")
    p.drawString(50, 710, f"GSTIN: {client.gstin if client.gstin else 'N/A'}")
    p.drawString(400, 725, f"Date: {datetime.now().strftime('%d-%m-%Y')}")

    # Bill Body
    p.line(50, 680, 550, 680)
    p.drawString(60, 665, "Description of Service")
    p.drawString(450, 665, "Amount (Rs.)")
    p.line(50, 660, 550, 660)

    p.drawString(60, 640, service)
    p.drawRightString(540, 640, f"{amount:.2f}")

    p.line(350, 600, 550, 600)
    p.drawString(360, 580, f"Taxable Value:")
    p.drawRightString(540, 580, f"{amount:.2f}")
    p.drawString(360, 560, f"GST ({gst_rate}%):")
    p.drawRightString(540, 560, f"{gst_amount:.2f}")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(360, 530, "NET PAYABLE:")
    p.drawRightString(540, 530, f"{total:.2f}")

    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 100, "Note: This is a computer-generated invoice.")
    p.drawRightString(550, 100, "For CA DEEPAK BHAYANA")
    p.drawRightString(550, 60, "(Authorized Signatory)")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Invoice_{client.name}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
