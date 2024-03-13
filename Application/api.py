from flask import Flask, request, jsonify, Blueprint
from .database import User, Categories, Products, Booking
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from . import api
from . import db
import re

api = Blueprint("api", __name__)

@api.route('/signing', methods=['POST'])
def signing():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password1 = data.get('password1')
    password2 = data.get('password2')
    user_type = data.get('user_type')
    
    if password1 != password2:
        return jsonify({'error': 'Passwords mismatched...'}), 400
    elif not (re.search("@gmail.com$", email)):
        return jsonify({'error': "Email should be in form 'example@gmail.com'"}), 400
    elif len(name) < 3:
        return jsonify({'error': "Username must be more than 2 Characters"}), 400
    else:
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({'error': 'Account already exists, Please Login...'}), 500
        else:
            try:
                if user_type == "is_manager":
                    new_user = User(
                        email=email,
                        name=name,
                        password=generate_password_hash(password1, method="sha256"),
                        is_manager=True,
                        is_customer=False,
                    )
                else:
                    new_user = User(
                        email=email,
                        name=name,
                        password=generate_password_hash(password1, method="sha256"),
                        is_customer=True,
                        is_manager=False,
                    )
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify({'error': 'An error occurred during Sign In process...'}), 500

            return jsonify({'message': 'Signup successful...'}), 200

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and user.password == password:
        return jsonify({'message': 'Login successful...'}), 200
    else:
        return jsonify({'error': 'Invalid details...'}), 401
    
    
@api.route('/logout', methods=['GET'])
@login_required
def logout():
    data = request.get_json()
    id = data.get('id')
    user = User.query.filter_by(id=id).first()
    
    if not user:
        return jsonify({"error": "Invalid User Id..."}), 401
    user.id = None
    db.session.commit()

    return jsonify({"message": "Logout successfully..."}), 200
    

@api.route('/delete_category/<int:C_id>', methods=['DELETE'])
@login_required
def delete_category(C_id):
    category = Categories.query.get(C_id)
    
    if not category:
        return jsonify({'error': 'Category not found...'}), 404

    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': 'Category deleted successfully...'}), 200


@api.route('/delete_product/<int:P_id>', methods=['DELETE'])
@login_required
def delete_product(P_id):
    product = Products.query.get(P_id)
    
    if not product:
        return jsonify({'error': 'Product not found...'}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': 'Product deleted successfully...'}), 200


@api.route('/update_category/<int:id>',methods = ['PUT'])
@login_required
def update_category(id):
    data = request.get_json()
    C_name = data.get('C_name')
    category = Categories.query.get(C_id=id).first()
    if not category:
        return jsonify({'error': 'Category not found...'}), 404
    elif current_user.id != category.C_user:
        return jsonify({'error': 'You do not have permission to update this category.'}), 400
    else:
        category.C_name = C_name
        if len(C_name) >= 2:
            try:
                db.session.commit()
                return jsonify({'message': 'Your Category is being updated...'}), 200
            except:
                db.session.rollback()
                return jsonify({'error': 'An error occurred while updating the category.'}), 500

        else:
            return jsonify({'error': 'Make sure all the fields are filled...'}), 400

    
    
@api.route('/update_product/<int:id>',methods = ['PUT'])
@login_required
def update_product(id):
    data = request.get_json()
    P_C_id = data.get("P_C_id")
    P_name = data.get("name")
    P_category = Categories.query.get(C_id = request.form.get('P_C_id')).first()
    unit = data.get("unit")
    rate_per_unit = data.get("rate_per_unit")
    quantity = data.get("quantity")
    
    product = Products.query.get(P_id=id).first()
    if not product:
        return jsonify({'error': 'Product not found...'}), 404
    elif current_user.id != product.P_user:
        return jsonify({'error': 'You do not have permission to update this product.'}), 400
    else:
        P_category = Categories.query.get(C_id = request.form.get('P_C_id')).first()
        product.P_name = P_name
        product.unit = unit
        product.P_C_id = P_C_id
        product.rate_per_unit = rate_per_unit
        product.quantity = quantity
        product.P_user = current_user.id
        product.P_C_name = P_category.C_name
        if len(P_name) >= 2 and (int(P_C_id) >=1):
            try:
                db.session.commit()
                return jsonify({'message': 'Your Product is being updated...'}), 200
            except:
                db.session.rollback()
                return jsonify({'error': 'An error occurred while updating the product.'}), 500
        else:
            return jsonify({'error': 'Make sure all the fields are filled...'}), 400



@api.route('/buy_product/<int:P_id>', methods=['POST'])
@login_required
def buy_product(P_id):
    data = request.get_json()
    total_quantity = data.get('total_quantity')
    product = Products.query.get(P_id=P_id).first()

    if not total_quantity:
        return jsonify({'error': 'Quantity must be provided...'}), 400

    if not product:
        return jsonify({'error': 'Product not found...'}), 404
    product.quantity = int(product.quantity) - int(total_quantity)

    booking = Booking(
                B_user=current_user.id,
                P_booked=product.P_id,
                C_booked=product.P_C_id,
                product_name=product.P_name,
                category_name=product.P_C_name,
                total_quantity=total_quantity,
                total_cost=int(product.rate_per_unit) * int(total_quantity) )
    try:
        db.session.add(booking)
        db.session.commit()
        return jsonify({'message': 'Your Product purchased successfully...'}), 200
    except:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while updating the category.'}), 500
    
    
@api.route('/my_booked_product/<int:id>', methods=['GET'])
@login_required
def my_booked_product(id):
    user = User.query.get(id)
    booking = Booking.query.get(id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not booking:
        return jsonify({'error': 'Your does not book any product... '}), 404

    products = user.products
    response_data = [{
        'id': product.P_id,
        'category_name': product.P_C_name,
        'product_name': product.P_name,
        'price': product.rate_per_unit,
        'quantity': product.quantity,
        'unit': product.unit
    } for product in products]
    return jsonify(response_data), 200


@api.route('/add_category', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    C_name = data.get('name')

    if not C_name :
        return jsonify({"error": "Category Name are required fields..."}), 400

    try:
        new_category = Categories(C_name=C_name, C_user=current_user.id )
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"message": "Category added successfully..."}), 200
    except:
        db.session.rollback()
        return jsonify({"error": "Failed to add the category."}), 500


@api.route('/add_product', methods=['POST'])
@login_required
def add_product():
    data = request.json
    P_name = data.get('P_name')
    P_C_id = data.get('P_C_id')
    unit = data.get('unit')
    rate_per_unit = data.get('rate_per_unit')
    quantity = data.get('quantity')
    P_category = Categories.query.filter_by(C_id = request.form.get('P_C_id')).first()

    if not P_name or not unit or not rate_per_unit or not quantity:
        return jsonify({"error": "All fields are required..."}), 400

    try:
        new_product = Products(
            P_name=P_name,
            P_C_name=P_category.C_name,
            P_user=current_user.id,
            unit=unit,
            rate_per_unit=rate_per_unit,
            quantity=quantity,
            P_C_id=P_C_id
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "Product added successfully."}), 200
    except:
        db.session.rollback()
        return jsonify({"error": "Failed to add the product."}), 500




