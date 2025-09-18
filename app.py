from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import sys

app = Flask(__name__)

# -------------------------
# Environment Variables
# -------------------------
MONGO_URI = os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")

if not MONGO_URI or not SECRET_KEY:
    print("⚠️ Missing MONGO_URI or SECRET_KEY! Falling back to local dev settings.", file=sys.stderr)
    # Local/dev fallback (not for production)
    MONGO_URI = "mongodb://localhost:27017/testdb"
    SECRET_KEY = "dev_secret_key"

app.secret_key = SECRET_KEY

# -------------------------
# MongoDB Connection
# -------------------------
try:
    # Atlas requires TLS
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    # Get DB name from URI, default = "expense_tracker"
    db_name = MONGO_URI.rsplit("/", 1)[-1].split("?")[0] or "expense_tracker"
    db = client[db_name]
    client.admin.command("ping")  # test connection
    print("✅ Connected to MongoDB:", db_name)
except Exception as e:
    print("❌ MongoDB connection failed:", e, file=sys.stderr)
    db = None

# Collections (safe fallback if DB fails)
users_collection = db["users"] if db else None
transactions_collection = db["transactions"] if db else None


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
        if not users_collection:
            flash("Database not available. Try again later.", "danger")
            return redirect(url_for("signup"))

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
        if not users_collection:
            flash("Database not available. Try again later.", "danger")
            return redirect(url_for("login"))

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

    if not transactions_collection:
        flash("Database not available. Try again later.", "danger")
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

    if not transactions_collection:
        flash("Database not available. Try again later.", "danger")
        return redirect(url_for("dashboard"))

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

    if not transactions_collection:
        flash("Database not available. Try again later.", "danger")
        return redirect(url_for("dashboard"))

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

    return render_template("edit_transaction.html", transaction=transaction)

# Delete Transaction
@app.route("/delete/<string:id>", methods=["GET", "POST"])
def delete_transaction(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if not transactions_collection:
        flash("Database not available. Try again later.", "danger")
        return redirect(url_for("dashboard"))

    transaction = transactions_collection.find_one({"_id": ObjectId(id), "user_id": session["user_id"]})
    if not transaction:
        flash("Transaction not found!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        transactions_collection.delete_one({"_id": ObjectId(id), "user_id": session["user_id"]})
        flash("Transaction deleted!", "success")
        return redirect(url_for("dashboard"))

    return render_template("delete_transaction.html", transaction=transaction)

# Profile
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if not users_collection:
        flash("Database not available. Try again later.", "danger")
        return redirect(url_for("dashboard"))

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

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
