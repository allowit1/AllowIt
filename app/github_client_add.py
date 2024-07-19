import requests
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

async def add_collaborator(repo, username, permission):
    
    db = get_database()
    token = db.tokens.find_one({"service": "github"})["token"]

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Define the URL for adding a collaborator
    url = f'https://api.github.com/repos/{repo}/collaborators/{username}'
    
    # Define the payload with the permission
    data = {
        'permission': permission
    }
    
    print(f'Adding {username} to {repo} with {permission} permission...')

    # Make the PUT request to add the collaborator
    response = requests.put(url, headers=headers, json=data)
    
    # Check the response status code
    if response.status_code == 201:
        print(f'Successfully added {username} to {repo} with {permission} permission.')
    elif response.status_code == 204:
        print(f'{username} is already a collaborator in {repo} with {permission} permission.')
    else:
        print(f'Failed to add {username} to {repo}. Status code: {response.status_code}')
        print(response.json())