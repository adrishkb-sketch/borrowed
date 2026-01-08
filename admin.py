from flask import Blueprint, render_template, request, redirect
from werkzeug.security import check_password_hash
from models import User, Payout, db
from datetime import datetime, timedelta

admin = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_EMAIL = "admin@borrowed.com"
ADMIN_PASSWORD = "admin123"  # demo only
@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['email'] == ADMIN_EMAIL and request.form['password'] == ADMIN_PASSWORD:
            return redirect('/admin/dashboard')
    return render_template('admin/login.html')
@admin.route('/dashboard')
def admin_dashboard():
    payouts = Payout.query.filter_by(status="pending").all()
    users = User.query.all()
    return render_template('admin/dashboard.html', payouts=payouts, users=users)
@admin.route('/approve-payout/<int:payout_id>')
def approve_payout(payout_id):
    payout = Payout.query.get_or_404(payout_id)
    user = User.query.get(payout.user_id)

    user.balance -= payout.amount
    payout.status = "approved"

    db.session.commit()
    return redirect('/admin/dashboard')
@admin.route('/ban-user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    user = User.query.get_or_404(user_id)

    days = int(request.form['days'])
    reason = request.form['reason']

    user.is_banned = True
    user.ban_reason = reason
    user.ban_until = datetime.utcnow() + timedelta(days=days)

    db.session.commit()
    return redirect('/admin/dashboard')
