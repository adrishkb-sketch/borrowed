from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models import db, User
from datetime import datetime
import requests
import os

auth = Blueprint('auth', __name__)

# ---------------- TOKEN UTILS ----------------
def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt="email-verify")


def send_verification_email(email, token):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": os.environ.get("BREVO_API_KEY")
    }

    verify_link = f"https://borrowed.onrender.com/verify/{token}"

    payload = {
        "sender": {
            "email": "no-reply@borrowed.com",
            "name": "Borrowed"
        },
        "to": [{"email": email}],
        "subject": "Verify your email",
        "htmlContent": f"""
            <h3>Welcome to Borrowed 👋</h3>
            <p>Please verify your email by clicking the button below:</p>
            <a href="{verify_link}"
               style="padding:10px 15px;
                      background:#2563eb;
                      color:#fff;
                      text-decoration:none;
                      border-radius:5px;">
                Verify Email
            </a>
            <p>This link expires in 1 hour.</p>
        """
    }

    requests.post(url, json=payload, headers=headers)


# ---------------- REGISTER ----------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if len(password) < 8:
            flash("Password must be at least 8 characters")
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for('auth.register'))

        hashed = generate_password_hash(password)
        user = User(email=email, password=hashed, email_verified=False)
        db.session.add(user)
        db.session.commit()

        token = generate_verification_token(email)
        send_verification_email(email, token)

        flash("Verification email sent. Please check your inbox.")
        return render_template('auth/verify.html', email=email)

    return render_template('auth/register.html')


# ---------------- VERIFY EMAIL ----------------
@auth.route('/verify/<token>')
def verify(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        email = serializer.loads(
            token,
            salt="email-verify",
            max_age=3600  # 1 hour
        )
    except SignatureExpired:
        return "Verification link expired."
    except BadSignature:
        return "Invalid verification link."

    user = User.query.filter_by(email=email).first()
    if not user:
        return "User not found."

    user.email_verified = True
    db.session.commit()

    flash("Email verified successfully. Please log in.")
    return redirect(url_for('auth.login'))


# ---------------- LOGIN ----------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        # ❌ Invalid credentials
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password")
            return redirect(url_for('auth.login'))

        # ❌ Email not verified
        if not user.email_verified:
            flash("Please verify your email first")
            return redirect(url_for('auth.login'))

        # 🚫 User banned
        if user.is_banned:
            if user.ban_until and datetime.utcnow() > user.ban_until:
                user.is_banned = False
                user.ban_reason = None
                user.ban_until = None
                db.session.commit()
            else:
                flash(
                    f"You are banned until {user.ban_until.strftime('%d %b %Y %H:%M')}. "
                    f"Reason: {user.ban_reason}"
                )
                return redirect(url_for('auth.login'))

        # ✅ Login
        login_user(user)

        if user.first_login:
            return redirect(url_for('auth.profile_setup'))

        return redirect('/')

    return render_template('auth/login.html')


# ---------------- PROFILE SETUP ----------------
@auth.route('/profile-setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.phone = request.form['phone']
        current_user.address = request.form['address']
        current_user.first_login = False
        db.session.commit()
        return redirect('/')

    return render_template('auth/profile_setup.html')


# ---------------- LOGOUT ----------------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
