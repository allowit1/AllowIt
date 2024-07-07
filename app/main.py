from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime, timedelta
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models using Pydantic
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
    phone: Optional[str] = None
    permissionLevel: str
    company: Optional[str] = None
    isAdmin: bool = False

class PermissionLevel(BaseModel):
    name: str
    permissions: Dict[str, List[str]]

# Sample data (you may want to move this to a separate file or database in a real application)
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

MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(MONGO_URL)
    app.database = app.mongodb_client["allowit123"]
    app.users_collection = app.database["users"]
    app.levels_collection = app.database["permission_levels"]

# Helper function to get user's company
async def get_user_company(email: str) -> str:
    user = await app.users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["company"]

# API endpoint to get system messages
@app.get("/messages/{email}", response_model=List[Message], tags=["messages"])
async def get_messages(email: str):
    company = await get_user_company(email)
    # In a real application, you'd fetch company-specific messages here
    return messages

# API endpoint to get recent permissions
@app.get("/permissions/{email}", response_model=List[Permission])
async def get_permissions(email: str):
    try:
        company = await get_user_company(email)
        collection_name = f"pending_{company}"
        permissions_cursor = app.database[collection_name].find({"mail": email}, {"_id": 0})
        permissions_list = list(permissions_cursor)
        return permissions_list
    except Exception as e:
        logger.error(f"Error retrieving permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# API endpoint to get available applications
@app.get("/applications", response_model=List[Application])
async def get_applications(email: Optional[str] = None):
    # All companies have the same applications for now
    return applications

# API endpoint to submit a permission request
@app.post("/permission-request")
async def submit_permission_request(request: PermissionRequest, email: str):
    try:
        logger.info(f"Received permission request: {request}")
        
        company = await get_user_company(email)
        collection_name = f"pending_{company}"
        
        new_permission = Permission(
            mail=email,
            user=email,
            application=f"Application {request.applicationId}",
            status="Pending",
            urgency=request.urgency,
            timeRemaining=None
        )

        result = app.database[collection_name].insert_one(new_permission.dict(exclude_unset=True))
        
        # Audit logging
        log_admin_action(email, "submit_permission_request", f"User {email} submitted a permission request for Application {request.applicationId}")
        
        return {"status": "success", "message": "Permission request submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error processing permission request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Root API endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the AllowIt API"}

# Admin Endpoints

# Get all users for a company
@app.get("/users", response_model=List[User])
async def get_users(email: str):
    company = await get_user_company(email)
    users = list(app.users_collection.find({"company": company}))
    for user in users:
        user['id'] = str(user['_id'])
        del user['_id']
    return users

@app.post("/users")
async def add_user(user: User, admin_email: str):
    try:
        admin = await app.users_collection.find_one({"email": admin_email})
        if not admin or not admin.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        user_dict = user.dict(exclude_unset=True)
        user_dict["company"] = admin["company"]  # Set the user's company to the admin's company
        
        if 'id' in user_dict:
            del user_dict['id']  # Remove id if present, let MongoDB generate it
        
        result = app.users_collection.insert_one(user_dict)
        
        # Audit logging
        log_admin_action(admin_email, "add_user", f"Admin {admin_email} added a new user: {user.email}")
        
        return {"id": str(result.inserted_id), "message": "User added successfully"}
    except Exception as e:
        logger.error(f"Error adding new user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    
# Update a user
@app.put("/users/{user_id}")
async def update_user(user_id: str, user: User, admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    user_dict = user.dict(exclude_unset=True)
    del user_dict['id']
    result = app.users_collection.update_one({"_id": ObjectId(user_id), "company": admin["company"]}, {"$set": user_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Audit logging
    log_admin_action(admin_email, "update_user", f"Admin {admin_email} updated user: {user_id}")
    
    return {"message": "User updated successfully"}

# Delete a user
@app.delete("/users/{user_id}")
async def delete_user(user_id: str, admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = app.users_collection.delete_one({"_id": ObjectId(user_id), "company": admin["company"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Audit logging
    log_admin_action(admin_email, "delete_user", f"Admin {admin_email} deleted user: {user_id}")
    
    return {"message": "User deleted successfully"}

# Get all permission levels for a company
@app.get("/permission-levels")
async def get_permission_levels():
    try:
        levels = list(app.levels_collection.find())
        for level in levels:
            level['id'] = str(level['_id'])
            del level['_id']
        return levels
    except Exception as e:
        logger.error(f"Error retrieving permission levels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a new permission level
@app.post("/permission-levels")
async def create_permission_level(level: PermissionLevel):
    try:
        print(f"Received data: {level}")  # Add this line
        # Your existing code to create the permission level
        return {"message": "Permission level created successfully"}
    except Exception as e:
        print(f"Error creating permission level: {str(e)}")  # Add this line
        raise HTTPException(status_code=422, detail=str(e))
    

# Update a permission level
@app.put("/permission-levels/{level_id}")
async def update_permission_level(level_id: str, level: PermissionLevel, admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    level_dict = level.dict(exclude_unset=True)
    del level_dict['id']
    result = app.levels_collection.update_one({"_id": ObjectId(level_id), "company": admin["company"]}, {"$set": level_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Permission level not found")
    
    # Audit logging
    log_admin_action(admin_email, "update_permission_level", f"Admin {admin_email} updated permission level: {level_id}")
    
    return {"message": "Permission level updated successfully"}

# Delete a permission level
@app.delete("/permission-levels/{level_id}")
async def delete_permission_level(level_id: str, admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = app.levels_collection.delete_one({"_id": ObjectId(level_id), "company": admin["company"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Permission level not found")
    
    # Audit logging
    log_admin_action(admin_email, "delete_permission_level", f"Admin {admin_email} deleted permission level: {level_id}")
    
    return {"message": "Permission level deleted successfully"}

# Get admin messages
@app.get("/admin-messages", response_model=List[Message])
async def get_admin_messages(admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # In a real application, you might fetch admin-specific messages here
    return messages

# Get pending requests for a company
@app.get("/pending-requests", response_model=List[Permission])
async def get_pending_requests(admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    collection_name = f"pending_{admin['company']}"
    pending_requests = list(app.database[collection_name].find({"status": "Pending"}))
    for request in pending_requests:
        request['id'] = str(request['_id'])
        del request['_id']
    return pending_requests

# Approve a request
@app.post("/approve-request/{request_id}")
async def approve_request(request_id: str, admin_email: str, reason: Optional[str] = None, expiryTime: Optional[int] = None):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    collection_name = f"pending_{admin['company']}"
    expiry_date = datetime.now() + timedelta(hours=expiryTime) if expiryTime else datetime.now() + timedelta(days=30)
    result = app.database[collection_name].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "Approved", "approvedDate": datetime.now(), "expiryDate": expiry_date, "adminReason": reason}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Audit logging
    log_admin_action(admin_email, "approve_request", f"Admin {admin_email} approved request: {request_id}")
    
    return {"message": "Request approved successfully"}

# Deny a request
@app.post("/deny-request/{request_id}")
async def deny_request(request_id: str, admin_email: str, reason: Optional[str] = None):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    collection_name = f"pending_{admin['company']}"
    result = app.database[collection_name].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "Denied", "deniedDate": datetime.now(), "adminReason": reason}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Audit logging
    log_admin_action(admin_email, "deny_request", f"Admin {admin_email} denied request: {request_id}")
    
    return {"message": "Request denied successfully"}

# Get approved permissions for a company
@app.get("/approved-permissions", response_model=List[Permission])
def get_approved_permissions(admin_email: str):
    admin = app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    collection_name = f"pending_{admin['company']}"
    approved_permissions = list(app.database[collection_name].find(
        {"status": "Approved", "expiryDate": {"$gt": datetime.now()}}
    ))
    for permission in approved_permissions:
        permission['id'] = str(permission['_id'])
        del permission['_id']
    return approved_permissions

# Revoke a permission
@app.post("/revoke-permission/{permission_id}")
async def revoke_permission(permission_id: str, admin_email: str):
    admin = await app.users_collection.find_one({"email": admin_email})
    if not admin or not admin.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    collection_name = f"pending_{admin['company']}"
    result = app.database[collection_name].update_one(
        {"_id": ObjectId(permission_id)},
        {"$set": {"status": "Revoked", "revokedDate": datetime.now()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Audit logging
    log_admin_action(admin_email, "revoke_permission", f"Admin {admin_email} revoked permission: {permission_id}")
    
    return {"message": "Permission revoked successfully"}

# Function to log admin actions
def log_admin_action(admin_email: str, action: str, description: str):
    log_entry = {
        "timestamp": datetime.now(),
        "admin_email": admin_email,
        "action": action,
        "description": description
    }
    app.database["admin_audit_log"].insert_one(log_entry)
    logger.info(f"Admin action logged: {description}")


@app.get("/user-details/{email}")
async def get_user_details(email: str):
    user = app.users_collection.find_one({"email": email})
    if user:
        return {
            "company": user.get("company", ""),
            "isAdmin": user.get("isAdmin", False),
            "name": user.get("name", "")
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")
    

@app.get("/add-test-user")
async def add_test_user():
    test_user = {
        "name": "Test User",
        "email": "yeretyn@gmail.com",
        "company": "Test Company",
        "isAdmin": False
    }
    result = await app.users_collection.insert_one(test_user)
    return {"message": "Test user added", "id": str(result.inserted_id)}

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)