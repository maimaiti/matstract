import os
import json
from pymongo import MongoClient

def open_db_connection():
    try:
        db_creds_filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'db_atlas.json')
        with open(db_creds_filename) as f:
            db_creds = json.load(f)

    except:
        db_creds = {"user": os.environ["ATLAS_USER"],
                    "pass": os.environ["ATLAS_USER_PASSWORD"],
                    "rest": os.environ["ATLAS_REST"],
                    "db": "tri_abstracts"}

    uri = "mongodb://{user}:{pass}@{rest}".format(**db_creds)
    mongo_client = MongoClient(uri, connect=False)
    db = mongo_client[db_creds["db"]]
    return db
