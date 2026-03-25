import os, io, random, smtplib, openpyxl
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from datetime import datetime
from email.message import EmailMessage

# 1. PEHLE APP DEFINE KARNA HAI
app = Flask(__name__)
app.secret_key = "CA_Deepak_Secure_99100"

# 2. DATABASE SETUP
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. MODELS
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    address = db.Column(db.Text)

with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username="admin").first():
        db.session.add(Admin(username="admin", password=generate_password_hash("admin123")))
        db.session.commit()

# 4. SARE ROUTES (Ab yahan 'app' use ho sakta hai)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash("Invalid Credentials!")
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    clients = Client.query.order_by(Client.id.desc()).all()
    return render_template('index.html', clients=clients)

@app.route('/add-client', methods=['POST'])
def add_client():
    if not session.get('logged_in'): return redirect(url_for('login'))
    new_client = Client(
        name=request.form.get('name'),
        gstin=request.form.get('gstin'),
        email=request.form.get('email'),
        contact=request.form.get('contact'),
        address=request.form.get('address')
    )
    db.session.add(new_client)
    db.session.commit()
    flash("Client Added!")
    return redirect(url_for('index'))

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    if not session.get('logged_in'): return redirect(url_for('login'))
    file = request.files.get('file')
    if file and file.filename.endswith('.xlsx'):
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            count = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row[0]: 
                    client = Client(
                        name=str(row[0]),
                        gstin=str(row[1]) if row[1] else "",
                        email=str(row[2]) if row[2] else "",
                        contact=str(row[3]) if row[3] else "",
                        address=str(row[4]) if row[4] else ""
                    )
                    db.session.add(client)
                    count += 1
            db.session.commit()
            flash(f"Success! {count} clients imported.")
        except Exception as e:
            flash(f"Error: {str(e)}")
    return redirect(url_for('index'))

@app.route('/create-bill/<int:client_id>')
def create_bill(client_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    client = Client.query.get(client_id)
    return render_template('create_bill.html', client=client)

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
    
    # Header Style (Professional Navy)
    p.setFillColorRGB(0, 0.13, 0.29)
    p.rect(0, 750, 600, 100, fill=1)
    
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(300, 800, "CA DEEPAK BHAYANA")
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 785, "Chartered Accountants | Paschim Vihar West Metro, Delhi - 110063")
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 720, "TAX INVOICE")
    p.setFont("Helvetica", 10)
    p.drawRightString(550, 720, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    
    p.line(50, 710, 550, 710)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, 690, f"BILL TO:")
    p.setFont("Helvetica", 11)
    p.drawString(50, 675, f"{client.name}")
    p.setFont("Helvetica", 9)
    p.drawString(50, 660, f"GSTIN: {client.gstin if client.gstin else 'N/A'}")
    
    # Table Header
    p.setFillColorRGB(0.95, 0.95, 0.95)
    p.rect(50, 600, 500, 20, fill=1)
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, 607, "Description of Service")
    p.drawRightString(540, 607, "Amount (INR)")
    
    p.setFont("Helvetica", 10)
    p.drawString(60, 580, service)
    p.drawRightString(540, 580, f"{amount:,.2f}")
    
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
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(550, 120, "For CA DEEPAK BHAYANA")
    p.drawRightString(550, 80, "Authorised Signatory")

    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Invoice_{client.name}.pdf", mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
