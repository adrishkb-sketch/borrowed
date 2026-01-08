from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import uuid
from datetime import datetime

auth = Blueprint('auth', __name__)

verification_tokens = {}

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
        user = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()

        token = str(uuid.uuid4())
        verification_tokens[token] = user.id

        print(f"🔗 VERIFY LINK: http://127.0.0.1:5000/verify/{token}")

        return render_template('auth/verify.html', email=email)

    return render_template('auth/register.html')


# ---------------- VERIFY EMAIL ----------------
@auth.route('/verify/<token>')
def verify(token):
    user_id = verification_tokens.get(token)
    if not user_id:
        return "Invalid or expired link"

    user = User.query.get(user_id)
    user.verified = True
    db.session.commit()

    return redirect(url_for('auth.login'))


# ---------------- LOGIN (UPDATED) ----------------
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
        if not user.verified:
            flash("Please verify your email first")
            return redirect(url_for('auth.login'))

        # 🚫 User is banned
        if user.is_banned:
            # If ban expired, auto-unban
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

        # ✅ Login allowed
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
