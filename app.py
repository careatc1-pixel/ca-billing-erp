import os, io, random, smtplib
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from datetime import datetime
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = "CA_Deepak_Secure_786"

# DATABASE CONNECTION
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELS
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(15))
    email = db.Column(db.String(100))

with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username="admin").first():
        db.session.add(Admin(username="admin", password=generate_password_hash("admin123")))
        db.session.commit()

# ROUTES
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash("Invalid Credentials")
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', clients=Client.query.all())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add-client', methods=['POST'])
def add_client():
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('name')
    if name:
        db.session.add(Client(name=name, gstin=request.form.get('gstin'), email=request.form.get('email')))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/create-bill/<int:client_id>')
def create_bill(client_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('create_bill.html', client=Client.query.get(client_id))

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
