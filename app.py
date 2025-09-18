from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# Use MongoDB Atlas connection string from environment variable
MONGO_URI = "mongodb+srv://prasannakuchipudi99_db_user:Prasanna%4055@cluster0.fmlug6m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
"
client = MongoClient(MONGO_URI)

# Select database and collection
db = client["mydatabase"]
collection = db["users"]

@app.route("/")
def home():
    return "Flask + MongoDB Atlas Deployment Successful 🚀"

@app.route("/add", methods=["POST"])
def add_user():
    data = request.json
    collection.insert_one(data)
    return jsonify({"message": "User added successfully!"})

@app.route("/users", methods=["GET"])
def get_users():
    users = list(collection.find({}, {"_id": 0}))
    return jsonify(users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
