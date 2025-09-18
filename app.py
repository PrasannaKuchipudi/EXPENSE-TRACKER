from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# Get MongoDB URI from Render Environment Variable
MONGO_URI = os.getenv("MONGO_URI")
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
    if not data:
        return jsonify({"error": "No data provided"}), 400
    collection.insert_one(data)
    return jsonify({"message": "User added successfully!"})

@app.route("/users", methods=["GET"])
def get_users():
    users = list(collection.find({}, {"_id": 0}))
    return jsonify(users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
