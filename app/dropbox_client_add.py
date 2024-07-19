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


def add_folder_member(folder_id, email, access_level='viewer'):

    db = get_database()
    token = db.tokens.find_one({"service": "dropbox"})["token"]

    headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

    url = 'https://api.dropboxapi.com/2/sharing/add_folder_member'
    data = {
        "shared_folder_id": folder_id,
        "members": [{
            "member": {
                ".tag": "email",
                "email": email
            },
            "access_level": {
                ".tag": access_level
            }
        }],
        "quiet": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))

    print(response.text)
    
    if response.status_code == 200:
        print(f'Successfully added {email} to folder {folder_id} with {access_level} permission.')
    else:
        print(f'Failed to add {email} to folder {folder_id}. Status code: {response.status_code}')
        print(response.json())



# # Example usage:
# folder_id = '3362330899'
# email = "maornoy1310@gmail.com"  # Replace with the email of the member

# # Add a member to the folder
# add_folder_member(folder_id, email, access_level='editor')