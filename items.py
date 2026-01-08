from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from models import Item, Order, db
import os
from werkzeug.utils import secure_filename
from datetime import date

items = Blueprint('items', __name__)

UPLOAD_FOLDER = 'static/uploads'


# ---------------- HOME / MARKETPLACE ----------------
@items.route('/')
@login_required
def home():
    today = date.today()
    all_items = Item.query.all()
    item_data = []

    for item in all_items:
        active_orders = Order.query.filter(
            Order.item_id == item.id,
            Order.status == "approved",
            Order.end_date >= today
        ).all()

        available = item.total_quantity - len(active_orders)

        next_available = None
        if available <= 0 and active_orders:
            next_available = min(o.end_date for o in active_orders)

        item_data.append({
            "item": item,
            "available": available,
            "next_available": next_available
        })

    return render_template('items/home.html', items=item_data)


# ---------------- ADD ITEM ----------------
@items.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        rate = float(request.form['rate'])
        quantity = int(request.form['quantity'])
        image = request.files['image']

        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))

        item = Item(
            owner_id=current_user.id,
            name=name,
            description=description,
            rate_per_day=rate,
            total_quantity=quantity,   # 🔥 CRITICAL
            image=filename
        )

        db.session.add(item)
        db.session.commit()

        return redirect('/')

    return render_template('items/add_item.html')
