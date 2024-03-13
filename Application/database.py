from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique = True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_manager = db.Column(db.Boolean, nullable=False)
    is_customer = db.Column(db.Boolean, nullable=False)
    categories = db.relationship('Categories')
    products = db.relationship('Products')
    booking = db.relationship('Booking')

class Categories(db.Model):
    C_id = db.Column(db.Integer, primary_key = True)
    C_name = db.Column(db.String(150), nullable=False)
    C_booking = db.relationship('Booking')
    C_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    P_C_rel = db.relationship('Products')

    
class Products(db.Model):
    P_id = db.Column(db.Integer, primary_key = True)
    P_name = db.Column(db.String(150), nullable=False)
    P_C_name = db.Column(db.String(150))
    unit = db.Column(db.String(50), nullable=False)
    rate_per_unit = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    P_booking = db.relationship('Booking')
    P_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    P_C_id = db.Column(db.Integer, db.ForeignKey('categories.C_id'))

class Booking(db.Model):
    B_id = db.Column(db.Integer, primary_key = True)
    total_quantity = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(150))
    category_name = db.Column(db.String(150))
    total_cost = db.Column(db.Integer, nullable=False)
    C_booked = db.Column(db.Integer, db.ForeignKey('categories.C_id'))
    P_booked = db.Column(db.Integer, db.ForeignKey('products.P_id'))
    B_user = db.Column(db.Integer, db.ForeignKey('user.id'))