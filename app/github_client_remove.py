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

def remove_collaborator(repo, username):

    db = get_database()
    token = db.tokens.find_one({"service": "github"})["token"]

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Define the URL for removing a collaborator
    url = f'https://api.github.com/repos/{repo}/collaborators/{username}'
    
    print(f'Removing {username} from {repo}...')

    # Make the DELETE request to remove the collaborator
    response = requests.delete(url, headers=headers)
    
    # Check the response status code
    if response.status_code == 204:
        print(f'Successfully removed {username} from {repo}.')
    elif response.status_code == 404:
        print(f'{username} is not a collaborator in {repo}.')
    else:
        print(f'Failed to remove {username} from {repo}. Status code: {response.status_code}')
        print(response.json())

# Example usage:
# repo = "allowit1/Example_Repo"
# username = "benayat1"

# # Remove collaborator
# remove_collaborator(repo, username)

# Example usage:
# repo = "allowit1/Example_Repo"
# username = "benayat1"

# # Remove collaborator
# remove_collaborator(repo, username)