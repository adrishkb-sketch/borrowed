from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    verified = db.Column(db.Boolean, default=False)

    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

    first_login = db.Column(db.Boolean, default=True)

    balance = db.Column(db.Float, default=0)

    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text)
    ban_until = db.Column(db.DateTime)


class Payout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    upi_id = db.Column(db.String(120))
    amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer)

    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    rate_per_day = db.Column(db.Float)
    image = db.Column(db.String(200))

    total_quantity = db.Column(db.Integer, default=1)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    borrower_id = db.Column(db.Integer)

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProductReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    order_id = db.Column(db.Integer)      # 🔒 prevents duplicate reviews
    reviewer_id = db.Column(db.Integer)

    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)       # 🔒 prevents duplicate reviews
    reviewed_user_id = db.Column(db.Integer)
    reviewer_id = db.Column(db.Integer)

    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
