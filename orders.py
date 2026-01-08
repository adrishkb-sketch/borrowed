from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

from models import (
    Item,
    Order,
    User,
    ProductReview,
    UserReview,
    db
)

orders = Blueprint('orders', __name__)
UPLOAD_FOLDER = 'static/uploads'


# ---------------- ITEM DETAIL ----------------
@orders.route('/item/<int:item_id>')
@login_required
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    today = date.today()

    active_orders = Order.query.filter(
        Order.item_id == item.id,
        Order.status == "approved",
        Order.end_date >= today
    ).all()

    available = item.total_quantity - len(active_orders)

    next_available = None
    if available <= 0 and active_orders:
        next_available = min(o.end_date for o in active_orders)

    reviews = ProductReview.query.filter_by(item_id=item.id).all()

    return render_template(
        'items/item_detail.html',
        item=item,
        available=available,
        next_available=next_available,
        reviews=reviews
    )


# ---------------- FAKE PAYMENT ----------------
@orders.route('/fake-payment/<int:item_id>', methods=['POST'])
@login_required
def fake_payment(item_id):
    item = Item.query.get_or_404(item_id)

    start = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

    amount = (end - start).days * item.rate_per_day

    order = Order(
        item_id=item.id,
        borrower_id=current_user.id,
        start_date=start,
        end_date=end,
        amount=amount,
        status="pending"
    )
    db.session.add(order)
    db.session.commit()

    return render_template(
        'orders/fake_payment.html',
        item=item,
        start=start,
        end=end,
        amount=amount
    )


# ---------------- DASHBOARD ----------------
@orders.route('/dashboard')
@login_required
def dashboard():
    owned_items = Item.query.filter_by(owner_id=current_user.id).all()
    item_ids = [i.id for i in owned_items]

    orders_list = Order.query.filter(Order.item_id.in_(item_ids)).all()

    requests = []
    earnings = 0

    for order in orders_list:
        borrower = User.query.get(order.borrower_id)
        item = Item.query.get(order.item_id)

        borrower_reviews = UserReview.query.filter_by(
            reviewed_user_id=borrower.id
        ).all()

        avg_rating = (
            round(sum(r.rating for r in borrower_reviews) / len(borrower_reviews), 1)
            if borrower_reviews else "No ratings"
        )

        if order.status == "approved":
            earnings += order.amount

        can_review_user = (
            order.status == "approved"
            and order.end_date < date.today()
            and not UserReview.query.filter_by(order_id=order.id).first()
        )

        requests.append({
            "order": order,
            "item": item,
            "borrower": borrower,
            "rating": avg_rating,
            "can_review_user": can_review_user
        })

    return render_template(
        'orders/dashboard.html',
        requests=requests,
        earnings=earnings
    )


# ---------------- APPROVE / DECLINE ----------------
@orders.route('/order/<int:order_id>/approve')
@login_required
def approve_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = "approved"

    owner = User.query.get(Item.query.get(order.item_id).owner_id)
    owner.balance += order.amount

    db.session.commit()
    return redirect('/dashboard')


@orders.route('/order/<int:order_id>/decline')
@login_required
def decline_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = "declined"
    db.session.commit()
    return redirect('/dashboard')


# ---------------- MY ORDERS ----------------
@orders.route('/my-orders')
@login_required
def my_orders():
    orders_list = Order.query.filter_by(borrower_id=current_user.id).all()

    data = []
    for order in orders_list:
        item = Item.query.get(order.item_id)
        owner = User.query.get(item.owner_id)

        reviewed = ProductReview.query.filter_by(order_id=order.id).first()

        data.append({
            "order": order,
            "item": item,
            "owner": owner,
            "can_review": order.status == "approved" and not reviewed
        })

    return render_template('orders/my_orders.html', orders=data)


# ---------------- REVIEW PRODUCT ----------------
@orders.route('/review-product/<int:order_id>', methods=['GET', 'POST'])
@login_required
def review_product(order_id):
    order = Order.query.get_or_404(order_id)

    if order.borrower_id != current_user.id or order.status != "approved":
        return "Not allowed"

    if ProductReview.query.filter_by(order_id=order.id).first():
        return "Already reviewed"

    if request.method == 'POST':
        image = request.files.get('image')
        filename = None

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        review = ProductReview(
            order_id=order.id,
            item_id=order.item_id,
            reviewer_id=current_user.id,
            rating=int(request.form['rating']),
            comment=request.form['comment'],
            image=filename
        )

        db.session.add(review)
        db.session.commit()
        return redirect(f"/item/{order.item_id}")

    return render_template('reviews/product_review.html', order=order)


# ---------------- REVIEW USER ----------------
@orders.route('/review-user/<int:order_id>', methods=['GET', 'POST'])
@login_required
def review_user(order_id):
    order = Order.query.get_or_404(order_id)
    item = Item.query.get(order.item_id)

    if item.owner_id != current_user.id:
        return "Not allowed"

    if order.end_date >= date.today():
        return "Rental period not finished"

    if UserReview.query.filter_by(order_id=order.id).first():
        return "Already reviewed"

    if request.method == 'POST':
        review = UserReview(
            order_id=order.id,
            reviewed_user_id=order.borrower_id,
            reviewer_id=current_user.id,
            rating=int(request.form['rating']),
            comment=request.form['comment']
        )

        db.session.add(review)
        db.session.commit()
        return redirect('/dashboard')

    return render_template('reviews/user_review.html', order=order)
