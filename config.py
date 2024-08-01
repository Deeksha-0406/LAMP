# config.py
import pymongo

def get_db():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["LAMP"]
    return db
