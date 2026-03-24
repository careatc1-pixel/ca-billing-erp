import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.pdfgen import canvas
from datetime import datetime
import io

app = Flask(__name__)

# DATABASE CONNECTION
# Render se link uthayega, nahi toh local chalega
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(15))
    email = db.Column(db.String(100))

# Table Banane ka Command
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    all_clients = Client.query.all()
    return render_template('index.html', clients=all_clients)

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

@app.route('/create-bill/<int:client_id>')
def create_bill(client_id):
    client = Client.query.get(client_id)
    return render_template('create_bill.html', client=client)

@app.route('/generate-pdf/<int:client_id>', methods=['POST'])
def generate_pdf(client_id):
    client = Client.query.get(client_id)
    service = request.form.get('service')
    amount = float(request.form.get('amount') or 0)
    gst_rate = float(request.form.get('gst_rate', 18))
    gst_amount = (amount * gst_rate) / 100
    total = amount + gst_amount

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(300, 800, "CA DEEPAK BHAYANA")
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 785, "Chartered Accountants")
    p.line(50, 770, 550, 770)
    p.drawString(50, 740, f"Client: {client.name}")
    p.drawString(400, 740, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    p.drawString(50, 680, f"Service: {service}")
    p.drawString(50, 660, f"Amount: Rs. {amount:.2f}")
    p.drawString(50, 640, f"GST ({gst_rate}%): Rs. {gst_amount:.2f}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 610, f"Total Payable: Rs. {total:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Invoice_{client.name}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
