from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "9f5d3a8c1b2e4d6f7a8b9c0d1e2f3a4b"  # Keep this secure
import os
client = MongoClient(os.environ.get("mongodb://localhost:27017/"))
app.secret_key = os.environ.get("9f5d3a8c1b2e4d6f7a8b9c0d1e2f3a4b")
# -------------------------
# MongoDB connection
# -------------------------
client = MongoClient("mongodb://localhost:27017/")  # default local MongoDB
db = client['expense_tracker']  # Database
users_collection = db['users']
transactions_collection = db['transactions']

# -------------------------
# Routes
# -------------------------

@app.route("/")
def home():
    return redirect(url_for("login"))

# Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if users_collection.find_one({"email": email}):
            flash("Email already exists. Try logging in.", "danger")
        else:
            users_collection.insert_one({
                "username": username,
                "email": email,
                "password": password
            })
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("signup.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_collection.find_one({"email": email, "password": password})
        if user:
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    transactions = list(transactions_collection.find({"user_id": session["user_id"]}))

    # Calculate totals
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    total_balance = total_income - total_expense

    return render_template("dashboard.html",
                           transactions=transactions,
                           username=session["username"],
                           total_balance=total_balance,
                           total_income=total_income,
                           total_expense=total_expense)

# Add Transaction
@app.route("/add", methods=["GET", "POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        amount = float(request.form["amount"])
        type_ = request.form["type"]
        date = request.form["date"]

        transactions_collection.insert_one({
            "user_id": session["user_id"],
            "title": title,
            "amount": amount,
            "type": type_,
            "date": date
        })
        flash("Transaction added!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_transaction.html")

# Edit Transaction
@app.route("/edit/<string:id>", methods=["GET", "POST"])
def edit_transaction(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    transaction = transactions_collection.find_one({"_id": ObjectId(id), "user_id": session["user_id"]})
    if not transaction:
        flash("Transaction not found!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"]
        amount = float(request.form["amount"])
        type_ = request.form["type"]
        date = request.form["date"]

        transactions_collection.update_one(
            {"_id": ObjectId(id), "user_id": session["user_id"]},
            {"$set": {"title": title, "amount": amount, "type": type_, "date": date}}
        )
        flash("Transaction updated!", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_expense.html", transaction=transaction)

# Delete Transaction
@app.route("/delete/<string:id>", methods=["GET", "POST"])
def delete_transaction(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    transaction = transactions_collection.find_one({"_id": ObjectId(id), "user_id": session["user_id"]})
    if not transaction:
        flash("Transaction not found!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        transactions_collection.delete_one({"_id": ObjectId(id), "user_id": session["user_id"]})
        flash("Transaction deleted!", "success")
        return redirect(url_for("dashboard"))

    return render_template("delete_transaction.html", transaction=transaction)

# Profile Page
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"_id": ObjectId(session["user_id"])})

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        users_collection.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$set": {"username": username, "email": email, "password": password}}
        )
        flash("Profile updated!", "success")
        return redirect(url_for("dashboard"))

    return render_template("profile.html", user=user)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
