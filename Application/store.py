from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .database import User, Categories, Products, Booking
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re

store = Blueprint("store", __name__)


@store.route("/")
def home():
    categories = Categories.query.all()
    products = Products.query.all()
    return render_template(
        "home.html",
        user=current_user,
        products=products,
        categories=categories,
    )


@store.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("store.home"))
            else:
                flash("Incorrect Password...", category="error")
        else:
            flash("Email does not exist, Please Register...", category="error")
    return render_template("login.html", user=current_user)


@store.route("/signing", methods=["GET", "POST"])
def signing():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        user_type = request.form.get("user_type")
        if password1 != password2:
            flash("Passwords mismatched...", category="error")
        elif not (re.search("@gmail.com$", email)):
            flash("Email should be in form 'example@gmail.com'", category="error")
        elif len(name) < 3:
            flash("Username must be more than 2 Characters", category="error")
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                flash("Account already exists, Please Login...", category="warning")
            else:
                if user_type == "is_manager":
                    new_user = User(
                        email=email,
                        name=name,
                        password=generate_password_hash(password1, method="sha256"),
                        is_manager=True,
                        is_customer=False,
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    flash("Account created for Manager!", category="success")
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
                    flash("Account created for Customer!", category="success")
                return redirect(url_for("store.home"))
                
    return render_template("signing.html", user=current_user)


@store.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("store.home"))


@store.route("/add_category", methods=["GET", "POST"])
@login_required
def add_category():
    if current_user.is_manager == True:
        if request.method == "POST":
            C_name = request.form.get("name")
            if len(C_name) >= 2:
                new_category = Categories(C_name=C_name, C_user=current_user.id)
                db.session.add(new_category)
                db.session.commit()

                flash("Your Category is being added", category="success")
                return redirect(url_for("store.my_product"))
            else:
                flash("Make sure all the fields are filled", category="error")
                return render_template("add_category.html", user=current_user)
        else:
            return render_template("add_category.html", user=current_user)
    return redirect(url_for("store.home"))


@store.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    categories = Categories.query.filter_by(C_user=int(current_user.id)).all()
    if current_user.is_manager == True:
        if request.method == "POST":
            P_C_id = request.form.get("P_C_id")
            P_name = request.form.get("name")
            P_category = Categories.query.filter_by(C_id = request.form.get('P_C_id')).first()
            unit = request.form.get("unit")
            rate_per_unit = request.form.get("rate_per_unit")
            quantity = request.form.get("quantity")
            if (len(P_name) >= 2) and (int(P_C_id) >=1):
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
                flash("Your Product is being added", category="success")
                return redirect(url_for("store.my_product"))
            else:
                flash("Make sure all the fields are filled", category="error")
                return render_template(
                    "add_product.html",
                    user=current_user,
                    categories=categories,
                )
        else:
            return render_template("add_product.html", user=current_user)
    return redirect(url_for("store.home"))


@store.route("/my_product")
@login_required
def my_product():
    if current_user.is_manager == True:
        categories = Categories.query.all()
        products = Products.query.all()
        return render_template(
            "my_product.html",
            user=current_user,
            categories=categories,
            products=products,
        )
    return redirect(url_for("store.home"))

@store.route("/buy_product/<int:P_id>", methods=["GET", "POST"])
@login_required
def buy_product(P_id):
    if current_user.is_customer == True:
        product_buy =Products.query.get(int(P_id))
        category_buy=Categories.query.get(int(P_id))
        if request.method == "POST":
            total_quantity = request.form.get("total_quantity")
            product_buy.quantity = int(product_buy.quantity) - int(total_quantity)
            buy_new_product = Booking(
                B_user=current_user.id,
                P_booked=product_buy.P_id,
                C_booked=product_buy.P_C_id,
                product_name=product_buy.P_name,
                category_name=product_buy.P_C_name,
                total_quantity=total_quantity,
                total_cost=int(product_buy.rate_per_unit) * int(total_quantity)         
            )
            db.session.add(buy_new_product)
            db.session.commit()
            
            flash("Your product have been booked successfully!", category="success")
            return redirect(url_for("store.my_booked_product"))
        else:
            return render_template(
                "buy_product.html", user=current_user, product=product_buy, category=category_buy
            )
    else:
        return redirect(url_for("store.home"))
    
    
@store.route("/my_booked_product")
@login_required
def my_booked_product():
    if current_user.is_customer == True:
        categories = Categories.query.all()
        products = Products.query.all()
        booking = Booking.query.all()
        return render_template(
            "my_booked_product.html",
            user=current_user,
            categories=categories,
            products=products,
            booking=booking
        )
    return redirect(url_for("store.home"))


@store.route("/delete_category/<int:id>")
@login_required
def delete_category(id):
    category = Categories.query.filter_by(C_id=id).first()
    if not category:
        flash("Category does not exist...", category="error")
    elif current_user.id != category.C_user:
        flash('You do not have permission to delete this category.', category='error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted.', category='success')
    return redirect(url_for('store.home'))

@store.route("/delete_product/<int:id>")
@login_required
def delete_product(id):
    product = Products.query.filter_by(P_id=id).first()
    if not product:
        flash("Product does not exist...", category="error")
    elif current_user.id != product.P_user:
        flash('You do not have permission to delete this product...', category='error')
    else:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted.', category='success')
    return redirect(url_for('store.home'))

@store.route('/update_category/<int:id>',methods = ['GET','POST'])
@login_required
def update_category(id):
    category = Categories.query.filter_by(C_id=id).first()
    if request.method == 'POST':
        if not category:
            flash("Category does not exist...", category="error")
        elif current_user.id != category.C_user:
            flash('You do not have permission to update this category.', category='error')
        else:
            db.session.delete(category)
            db.session.commit()

            C_name = request.form.get("name")
            if len(C_name) >= 2:
                new_category = Categories(C_name=C_name, C_user=current_user.id)
                db.session.add(new_category)
                db.session.commit()

                flash("Your Category is being updated", category="success")
                return redirect(url_for("store.my_product"))
            else:
                flash("Make sure all the fields are filled", category="error")
                return render_template("add_category.html", user=current_user)
    else:
        return render_template("add_category.html", user=current_user)
    return redirect(url_for("store.home"))
    
    
@store.route('/update_product/<int:id>',methods = ['GET','POST'])
@login_required
def update_product(id):
    product = Products.query.filter_by(P_id=id).first()
    categories = Categories.query.filter_by(C_user=int(current_user.id)).all()

    if request.method == 'POST':
        if not product:
            flash("Product does not exist...", category="error")
        elif current_user.id != product.P_user:
            flash('You do not have permission to update this product.', category='error')
        else:
            db.session.delete(product)
            db.session.commit()

            P_C_id = request.form.get("P_C_id")
            P_name = request.form.get("name")
            P_category = Categories.query.filter_by(C_id = request.form.get('P_C_id')).first()
            unit = request.form.get("unit")
            rate_per_unit = request.form.get("rate_per_unit")
            quantity = request.form.get("quantity")
            if (len(P_name) >= 2) and (int(P_C_id) >=1):
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
                flash("Your Product is being updated...", category="success")
                return redirect(url_for("store.my_product"))
            else:
                flash("Make sure all the fields are filled", category="error")
                return render_template(
                    "add_product.html",
                    user=current_user,
                    categories=categories,
                )
    else:
        return render_template("add_product.html", user=current_user, categories=categories)
    return redirect(url_for("store.home"))






        