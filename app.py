import os
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from datetime import datetime
import io

app = Flask(__name__)
app.secret_key = "CA_Deepak_Secret_Key_123" # Session secure rakhne ke liye

# DATABASE CONNECTION
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. Admin Table (Login ke liye)
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# 2. Client Table
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(15))
    email = db.Column(db.String(100))

# Table banana aur default login create karna
with app.app_context():
    db.create_all()
    # Agar koi admin nahi hai, toh default login banayein
    if not Admin.query.filter_by(username="admin").first():
        hashed_pw = generate_password_hash("admin123", method='pbkdf2:sha256')
        new_admin = Admin(username="admin", password=hashed_pw)
        db.session.add(new_admin)
        db.session.commit()

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash("Invalid ID or Password!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    all_clients = Client.query.all()
    return render_template('index.html', clients=all_clients)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_user = request.form.get('new_username')
        new_pass = request.form.get('new_password')
        admin = Admin.query.first()
        if new_user: admin.username = new_user
        if new_pass: admin.password = generate_password_hash(new_pass, method='pbkdf2:sha256')
        db.session.commit()
        flash("Login ID/Password Updated Successfully!")
        return redirect(url_for('index'))
    
    return render_template('settings.html')

@app.route('/add-client', methods=['POST'])
def add_client():
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('name')
    if name:
        new_client = Client(name=name, gstin=request.form.get('gstin'), email=request.form.get('email'))
        db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/create-bill/<int:client_id>')
def create_bill(client_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    client = Client.query.get(client_id)
    return render_template('create_bill.html', client=client)

@app.route('/generate-pdf/<int:client_id>', methods=['POST'])
def generate_pdf(client_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    # (Purana PDF generation code yahan rahega)
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
    p.drawString(50, 740, f"Client: {client.name}")
    p.drawString(50, 720, f"Total: Rs. {total:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Invoice_{client.name}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
