from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select/create a database
db = client["mydatabase"]

# Select/create a collection
collection = db["users"]

# Insert a test document
result = collection.insert_one({"name": "Alice", "email": "alice@example.com"})

print("✅ Connected to MongoDB!")
print("Inserted document ID:", result.inserted_id)
