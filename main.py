from flask import render_template, request, url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from models import User, app, db, EshopItem, Cart
import stripe

login_manager = LoginManager()
login_manager.init_app(app)
stripe.api_key = 'get_your_strike_key_here'
line_items = []


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CREATE TABLE
# db.create_all()


@app.route('/')
def home():
    eshop_items = EshopItem.query.all()
    return render_template("index.html", logged_in=current_user.is_authenticated, eshop_items=eshop_items)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url='http://127.0.0.1:5000/success/',
        cancel_url='https://templates/cancel.html',
    )

    return redirect(session.url, code=303)


@app.route('/success/')
def success():
    return render_template("success.html", user=current_user, items=line_items)


def calculate_final_price():
    global line_items
    line_items = []
    price = 0.0
    cart_user_items = Cart.query.filter_by(user_id=current_user.id).all()
    for item in cart_user_items:
        price += (float(EshopItem.query.filter_by(id=item.items).first().price) * float(item.quantity))
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': EshopItem.query.filter_by(id=item.items).first().name, },
                'unit_amount': int(str(int(EshopItem.query.filter_by(id=item.items).first().price)) + "00"), },
            'quantity': item.quantity, }, )
        return price


@app.route('/detail/<item_id>')
def detail(item_id):
    item = EshopItem.query.filter_by(id=item_id).first()
    return render_template("detail.html", logged_in=current_user.is_authenticated, item=item)


@app.route('/cart/')
def cart():
    final_price = calculate_final_price()
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    eshop_items = EshopItem.query.all()
    return render_template("cart.html",
                           logged_in=current_user.is_authenticated,
                           cart_items=cart_items,
                           eshop_items=eshop_items,
                           final_price=final_price)


@app.route('/add_to_cart/<item_id>')
def add_to_cart(item_id):
    if is_item_in_cart(item_id):
        item_to_update = Cart.query.filter_by(items=item_id).first()
        item_to_update.quantity += 1
        db.session.commit()
    else:
        new_card_record = Cart(items=item_id, quantity=1, user_id=current_user.id)
        db.session.add(new_card_record)
        db.session.commit()
    return redirect(url_for("home"))


def is_item_in_cart(item_id):
    cart_user_items = Cart.query.filter_by(user_id=current_user.id).all()
    for item in cart_user_items:
        if int(item.items) == int(item_id):
            return item.id
        else:
            return False


@app.route('/delete_from_cart/<item_id>')
def delete_from_cart(item_id):
    item_to_delete = Cart.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for("cart"))


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
