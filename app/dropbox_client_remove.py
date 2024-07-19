import requests
import json
from pymongo import MongoClient
import os

mongodb_client = None
database = None
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

def get_database():
    global mongodb_client, database
    if mongodb_client is None:
        mongodb_client = MongoClient(MONGO_URL)
        database = mongodb_client["allowit123"]
    return database


def remove_folder_member(folder_id, email):

    db = get_database()
    token = db.tokens.find_one({"service": "dropbox"})["token"]

    headers = {
     'Authorization': f'Bearer {token}',
     'Content-Type': 'application/json'
    }

    url = 'https://api.dropboxapi.com/2/sharing/remove_folder_member'
    data = {
        "shared_folder_id": folder_id,
        "member": {
            ".tag": "email",
            "email": email
        },
        "leave_a_copy": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print(f'Successfully removed {email} from folder {folder_id}.')
    else:
        print(f'Failed to remove {email} from folder {folder_id}. Status code: {response.status_code}')
        print(response.json())