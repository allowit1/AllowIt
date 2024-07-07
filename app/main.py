# Import necessary libraries
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime, timedelta
import logging
from bson.errors import InvalidId

# Set up logging to track errors and information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
# This is necessary for the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. In production, you should specify your frontend URL.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define data models using Pydantic for data validation
# These models define the structure of our data

class Message(BaseModel):
    content: str

class Permission(BaseModel):
    id: Optional[str] = None
    mail: Optional[str] = None
    user: str
    application: str
    status: str
    urgency: str
    timeRemaining: Optional[str] = None
    expiryDate: Optional[datetime] = None

class Application(BaseModel):
    id: str
    name: str
    icon: str
    href: str
    permissions: List[str]

class PermissionRequest(BaseModel):
    applicationId: str
    reason: Optional[str] = None
    urgency: str
    time: Optional[str] = None
    days: Optional[str] = None

class User(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    phone: str
    permissionLevel: str

class PermissionLevel(BaseModel):
    id: Optional[str] = None
    name: str
    permissions: Dict[str, List[str]]

# Sample data (in a real application, this would typically come from a database)
messages = [
    Message(content="Welcome to AllowIt!"),
    Message(content="Your account has been created successfully.")
]

applications = [
    Application(id="app1", name="Application 1", icon="../images/app-icon.png", href="https://github.com/", permissions=["read", "write", "delete"]),
    Application(id="app2", name="Application 2", icon="../images/app-icon.png", href="https://github.com/", permissions=["read", "write"]),
    Application(id="app3", name="Application 3", icon="../images/app-icon.png", href="https://github.com/", permissions=["read"]),
    Application(id="app4", name="Application 4", icon="../images/app-icon.png", href="https://github.com/", permissions=["read", "write", "delete", "admin"]),
    Application(id="app5", name="Application 5", icon="../images/app-icon.png", href="https://github.com/", permissions=["read", "write"])
]

# Set up MongoDB connection
company = "AllowIt"
collection_name = f"pending_{company}"
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

@app.on_event("startup")
def startup_db_client():
    """
    This function runs when the application starts up.
    It initializes the MongoDB client and connects to the necessary databases and collections.
    """
    # Initialize MongoDB client
    app.mongodb_client = MongoClient(MONGO_URL)
    
    # Connect to the main database
    app.database = app.mongodb_client["allowit123"]
    
    # Connect to specific collections within the database
    app.collection = app.database["permissions"]
    app.users_collection = app.database["users"]
    app.levels_collection = app.database["permission_levels"]

# API Routes

@app.get("/messages/{email}", response_model=List[Message], tags=["messages"])
async def get_messages(email: str):
    """
    Retrieve system messages for a user.
    
    Parameters:
    - email: The email of the user requesting messages
    
    Returns:
    - A list of Message objects
    """
    # In a real application, you might filter messages based on the user's email
    return messages

@app.get("/permissions/{email}", response_model=List[Permission])
async def get_permissions(email: str):
    """
    Retrieve permissions for a specific user.
    
    Parameters:
    - email: The email of the user whose permissions are being requested
    
    Returns:
    - A list of Permission objects associated with the user
    """
    try:
        # Search for permissions in the database where the 'mail' field matches the provided email
        permissions_cursor = app.database[collection_name].find({"mail": email}, {"_id": 0})
        
        # Convert the cursor to a list of permissions
        permissions_list = list(permissions_cursor)
        return permissions_list
    except Exception as e:
        # Log the error and raise an HTTP exception
        logger.error(f"Error retrieving permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/applications", response_model=List[Application])
async def get_applications(email: Optional[str] = None):
    """
    Retrieve all available applications.
    
    Parameters:
    - email: Optional. The email of the user requesting applications (not used in this implementation)
    
    Returns:
    - A list of Application objects
    """
    # In a real application, you might filter applications based on the user's permissions
    return applications

@app.post("/permission-request")
async def submit_permission_request(request: PermissionRequest, email: str):
    """
    Submit a new permission request.
    
    Parameters:
    - request: A PermissionRequest object containing details of the request
    - email: The email of the user submitting the request
    
    Returns:
    - A dictionary containing the status of the request and the ID of the new permission
    """
    try:
        # Log the received request for debugging purposes
        logger.info(f"Received permission request: {request}")
        
        # Create a new Permission object
        new_permission = Permission(
            mail=email,
            user=email,  # Assuming email is used as user identifier
            application=f"Application {request.applicationId}",
            status="Pending",
            urgency=request.urgency,
            timeRemaining=None
        )

        # Insert the new permission into the database
        result = app.database[collection_name].insert_one(new_permission.dict(exclude_unset=True))
        
        # Return a success message with the ID of the new permission
        return {"status": "success", "message": "Permission request submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        # Log the error and raise an HTTP exception
        logger.error(f"Error processing permission request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    
    Returns:
    - A welcome message
    """
    return {"message": "Welcome to the AllowIt API"}

# Admin Endpoints

@app.get("/users", response_model=List[User])
async def get_users():
    """
    Retrieve all users.
    
    Returns:
    - A list of User objects
    """
    # Fetch all users from the database
    users = list(app.users_collection.find())
    
    # Convert MongoDB ObjectId to string for each user
    for user in users:
        user['id'] = str(user['_id'])
        del user['_id']
    return users

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """
    Retrieve a specific user by ID.
    """
    user = app.users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user['id'] = str(user['_id'])
    del user['_id']
    return user

@app.post("/users")
async def add_user(user: User):
    """
    Add a new user.
    
    Parameters:
    - user: A User object containing the details of the new user
    
    Returns:
    - A dictionary containing the ID of the new user
    """
    # Convert the User object to a dictionary
    user_dict = user.dict(exclude_unset=True)
    
    # If no ID is provided, generate a new MongoDB ObjectId
    if 'id' not in user_dict:
        user_dict['_id'] = ObjectId()
    else:
        # If an ID is provided, convert it to MongoDB ObjectId
        user_dict['_id'] = ObjectId(user_dict['id'])
        del user_dict['id']
    
    # Insert the new user into the database
    result = app.users_collection.insert_one(user_dict)
    return {"id": str(result.inserted_id)}

@app.put("/users/{user_id}")
async def update_user(user_id: str, user: User):
    """
    Update an existing user.
    """
    user_dict = user.dict(exclude_unset=True)
    if 'id' in user_dict:
        del user_dict['id']  # Remove id from update data
    result = app.users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """
    Delete a user.
    """
    result = app.users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@app.get("/permission-levels", response_model=List[PermissionLevel])
async def get_permission_levels():
    """
    Retrieve all permission levels.
    
    Returns:
    - A list of PermissionLevel objects
    """
    # Fetch all permission levels from the database
    levels = list(app.levels_collection.find())
    
    # Convert MongoDB ObjectId to string for each level
    for level in levels:
        level['id'] = str(level['_id'])
        del level['_id']
    return levels

@app.get("/permission-levels/{level_id}", response_model=PermissionLevel)
async def get_permission_level(level_id: str):
    """
    Retrieve a specific permission level by ID.
    
    Parameters:
    - level_id: The ID of the permission level to retrieve
    
    Returns:
    - A PermissionLevel object
    """
    # Find the permission level in the database by its ID
    level = app.levels_collection.find_one({"_id": ObjectId(level_id)})
    
    # If the level is not found, raise a 404 error
    if level is None:
        raise HTTPException(status_code=404, detail="Permission level not found")
    
    # Convert MongoDB ObjectId to string
    level['id'] = str(level['_id'])
    del level['_id']
    return level

@app.post("/permission-levels")
async def add_permission_level(level: PermissionLevel):
    """
    Add a new permission level.
    
    Parameters:
    - level: A PermissionLevel object containing the details of the new level
    
    Returns:
    - A dictionary containing the ID of the new permission level
    """
    # Log the received permission level data for debugging
    logger.info(f"Received permission level data: {level}")
    
    # Convert the PermissionLevel object to a dictionary
    level_dict = level.dict(exclude_unset=True)
    
    # If no ID is provided, generate a new MongoDB ObjectId
    if 'id' not in level_dict:
        level_dict['_id'] = ObjectId()
    else:
        # If an ID is provided, convert it to MongoDB ObjectId
        level_dict['_id'] = ObjectId(level_dict['id'])
        del level_dict['id']
    
    # Insert the new permission level into the database
    result = app.levels_collection.insert_one(level_dict)
    return {"id": str(result.inserted_id)}

@app.put("/permission-levels/{level_id}")
async def update_permission_level(level_id: str, level: PermissionLevel):
    """
    Update an existing permission level.
    
    Parameters:
    - level_id: The ID of the permission level to update
    - level: A PermissionLevel object containing the updated details
    
    Returns:
    - A message indicating success
    """
    # Convert the PermissionLevel object to a dictionary
    level_dict = level.dict(exclude_unset=True)
    
    # Remove the ID from the update data if present
    if 'id' in level_dict:
        del level_dict['id']
    
    # Update the permission level in the database
    result = app.levels_collection.update_one({"_id": ObjectId(level_id)}, {"$set": level_dict})
    
    # If no level was modified, raise a 404 error
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Permission level not found")
    return {"message": "Permission level updated successfully"}

@app.delete("/permission-levels/{level_id}")
async def delete_permission_level(level_id: str):
    """
    Delete a permission level.
    
    Parameters:
    - level_id: The ID of the permission level to delete
    
    Returns:
    - A message indicating success
    """
    # Delete the permission level from the database
    result = app.levels_collection.delete_one({"_id": ObjectId(level_id)})
    
    # If no level was deleted, raise a 404 error
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Permission level not found")
    return {"message": "Permission level deleted successfully"}

@app.get("/admin-messages", response_model=List[Message])
async def get_admin_messages():
    """
    Retrieve admin-specific messages.
    
    Returns:
    - A list of Message objects
    """
    # In a real application, you might fetch admin-specific messages from a database
    return messages

@app.get("/pending-requests", response_model=List[Permission])
async def get_pending_requests():
    """
    Retrieve all pending permission requests.
    
    Returns:
    - A list of Permission objects with status "Pending"
    """
    # Fetch all pending requests from the database
    pending_requests = list(app.database[collection_name].find({"status": "Pending"}))
    
    # Convert MongoDB ObjectId to string for each request
    for request in pending_requests:
        request['id'] = str(request['_id'])
        del request['_id']
    return pending_requests

@app.post("/approve-request/{request_id}")
async def approve_request(request_id: str, reason: Optional[str] = None, expiryTime: Optional[int] = None):
    """
    Approve a pending permission request.
    
    Parameters:
    - request_id: The ID of the request to approve
    - reason: Optional reason for approval
    - expiryTime: Optional expiry time in hours
    
    Returns:
    - A message indicating success
    """
    # Calculate the expiry date
    if expiryTime:
        expiry_date = datetime.now() + timedelta(hours=expiryTime)
    else:
        expiry_date = datetime.now() + timedelta(days=30)  # Default to 30 days if no expiry time is provided
    
    # Update the request in the database
    result = app.database[collection_name].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": "Approved", 
            "approvedDate": datetime.now(), 
            "expiryDate": expiry_date, 
            "adminReason": reason
        }}
    )
    
    # If no request was modified, raise a 404 error
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Request approved successfully"}

@app.post("/deny-request/{request_id}")
async def deny_request(request_id: str, reason: Optional[str] = None):
    """
    Deny a pending permission request.
    
    Parameters:
    - request_id: The ID of the request to deny
    - reason: Optional reason for denial
    
    Returns:
    - A message indicating success
    """
    # Update the request in the database
    result = app.database[collection_name].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": "Denied", 
            "deniedDate": datetime.now(), 
            "adminReason": reason
        }}
    )
    
    # If no request was modified, raise a 404 error
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Request denied successfully"}

@app.get("/approved-permissions", response_model=List[Permission])
async def get_approved_permissions():
    """
    Retrieve all approved permissions that haven't expired.
    
    Returns:
    - A list of Permission objects with status "Approved" and not expired
    """
    # Fetch all approved permissions that haven't expired from the database
    approved_permissions = list(app.database[collection_name].find({
        "status": "Approved",
        "expiryDate": {"$gt": datetime.now()}
    }))
    
    # Convert MongoDB ObjectId to string for each permission
    for permission in approved_permissions:
        permission['id'] = str(permission['_id'])
        del permission['_id']
    return approved_permissions

@app.post("/revoke-permission/{permission_id}")
async def revoke_permission(permission_id: str):
    """
    Revoke an approved permission.
    
    Parameters:
    - permission_id: The ID of the permission to revoke
    
    Returns:
    - A message indicating success
    """
    # Update the permission in the database
    result = app.database[collection_name].update_one(
        {"_id": ObjectId(permission_id)},
        {"$set": {
            "status": "Revoked", 
            "revokedDate": datetime.now()
        }}
    )
    
    # If no permission was modified, raise a 404 error
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission revoked successfully"}

# Helper function to convert MongoDB ObjectId to string
def convert_objectid_to_str(item):
    """
    Convert MongoDB ObjectId to string in a dictionary.
    
    Parameters:
    - item: A dictionary containing an '_id' field with ObjectId
    
    Returns:
    - The same dictionary with '_id' converted to a string 'id'
    """
    item['id'] = str(item['_id'])
    del item['_id']
    return item

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)