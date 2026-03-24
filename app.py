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

# --- MODELS ---
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

# --- OTP HELPER ---
def send_otp_email(otp):
    msg = EmailMessage()
    msg.set_content(f"Your OTP for CA Deepak Bhayana ERP Settings is: {otp}")
    msg['Subject'] = 'ERP Security OTP'
    msg['From'] = os.environ.get('EMAIL_USER')
    msg['To'] = 'cadeepakbhayana1@gmail.com'

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.environ.get('EMAIL_USER'), os.environ.get('EMAIL_PASS'))
            smtp.send_message(msg)
        return True
    except:
        return False

# --- ROUTES ---
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

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_otp':
            otp = str(random.randint(100000, 999999))
            session['temp_otp'] = otp
            if send_otp_email(otp):
                flash("OTP sent to cadeepakbhayana1@gmail.com")
                return render_template('settings.html', otp_sent=True)
            else:
                flash("Error sending email. Check App Password.")
        
        elif action == 'verify_otp':
            user_otp = request.form.get('otp')
            if user_otp == session.get('temp_otp'):
                admin = Admin.query.first()
                if request.form.get('new_user'): admin.username = request.form.get('new_user')
                if request.form.get('new_pass'): admin.password = generate_password_hash(request.form.get('new_pass'))
                db.session.commit()
                session.pop('temp_otp', None)
                flash("Credentials Updated!")
                return redirect(url_for('index'))
            flash("Invalid OTP!")
            
    return render_template('settings.html', otp_sent=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# (Yahan client add aur pdf generation routes purane wale paste kar dein)

if __name__ == '__main__':
    app.run(debug=True)
