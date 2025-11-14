from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "mysecret"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mysql11022004@",
    database="simple_store"
)
cursor = db.cursor(dictionary=True)

if not os.path.exists("static/images"):
    os.makedirs("static/images")
if not os.path.exists("sent_emails"):
    os.makedirs("sent_emails")

@app.route("/")
def home():
    cursor.execute("SELECT * FROM products")
    all_products = cursor.fetchall()
    return render_template("home.html", products=all_products)

@app.route("/add_to_cart/<int:pid>")
def add_to_cart(pid):
    cursor.execute("SELECT * FROM products WHERE id = %s", (pid,))
    product = cursor.fetchone()

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(product)
    session.modified = True

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart_items = session.get("cart", [])
    total = sum(float(item["price"]) for item in cart_items)
    return render_template("cart.html", cart=cart_items, total=total)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        address = request.form["address"]
        cart_items = session.get("cart", [])

        total = sum(float(item["price"]) for item in cart_items)

        with open(f"sent_emails/order_{name}.txt", "w") as f:
            f.write(f"Order by: {name}\nEmail: {email}\nAddress: {address}\n")
            f.write("Items:\n")
            for item in cart_items:
                f.write(f"{item['name']} - ₹{item['price']}\n")
            f.write(f"Total: ₹{total}\n")

        session.pop("cart", None)

        return render_template("thankyou.html", name=name)

    return render_template("checkout.html")


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        admin = cursor.fetchone()
        if admin:
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            return "Wrong username or password!"
    return render_template("admin_login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        desc = request.form["description"]
        image_url = request.form["image_url"]  

        cursor.execute(
            "INSERT INTO products (name, price, description, image) VALUES (%s, %s, %s, %s)",
            (name, price, desc, image_url)
        )
        db.commit()
        return redirect(url_for("admin"))

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template("admin.html", products=products)


@app.route("/delete_product/<int:pid>")
def delete_product(pid):
    cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
    db.commit()
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
