import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail

from models import db, User
from auth import auth
from items import items
from orders import orders
from admin import admin

# ---------------- APP ----------------
app = Flask(__name__)

# ---------------- PATH CONFIG ----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------- CORE CONFIG ----------------
app.config['SECRET_KEY'] = os.environ.get(
    "SECRET_KEY", "borrowed-secret-key"
)

# Database: PostgreSQL in production, SQLite locally
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI",
    "sqlite:///" + os.path.join(BASE_DIR, "database.db")
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ---------------- MAIL (SAFE DEFAULTS) ----------------
app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

# ---------------- INIT EXTENSIONS ----------------
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

mail = Mail(app)

# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- BLUEPRINTS ----------------
app.register_blueprint(auth)
app.register_blueprint(items)
app.register_blueprint(orders)
app.register_blueprint(admin)

# ---------------- DB INIT ----------------
with app.app_context():
    db.create_all()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
