from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    cart_items = db.relationship('Cart', backref='user', lazy=True)


class EshopItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    name = db.Column(db.String(100))
    image = db.Column(db.String)
    description = db.Column(db.Text(10000))
    stock = db.Column(db.Integer)
    price = db.Column(db.Float)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
