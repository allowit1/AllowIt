from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
from pymongo import MongoClient
import os
from bson import ObjectId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

class Messages(BaseModel):
    email: str
    messages :List[str]

class Permission(BaseModel):
    name : str
    urgency : str
    status: str
    timeRemaining: Optional[str] = None

class Application(BaseModel):
    id: str
    name: str
    icon: str
    href: str
    permissions: List[str]

class PermissionRequest(BaseModel):
    request: str
    urgency: str
    timeRemaining: Optional[str] = None


class User(BaseModel):
    _id: str
    name: str
    email: str
    phone: str
    permissionLevel: str
    isAdmin: bool

class PermissionLevel(BaseModel):
    id: str
    name: str
    permissions: Dict[str, List[str]]

# Connect to MongoDB when the application starts
@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(MONGO_URL)
    app.database = app.mongodb_client["allowit123"]

    # app.database.permissions.insert_one({ "email": "yyeret@g.jct.ac.il",  "permissions": [{"name": "AB", "urgency": "low", "timeRemaining": "2 days", "status": "pending"} ,{"name": "cd", "urgency": "high", "status": "approved"}]})
   
    # app.database.users.insert_one({
    #     "name": "Admin",
    #     "email": "yeretyn@gmail.com",
    #     "phone": "1234567890",
    #     "permissionLevel": "admin",
    #     "isAdmin": True})

    # app.database.users.insert_one({
    #     "name": "Admin",
    #     "email": "yyeret@g.jct.ac.il",
    #     "phone": "1234567890",
    #     "permissionLevel": "admin",
    #     "isAdmin": False})

    # app.database.messages.insert_one({
    #     "email": "yyeret@g.jct.ac.il",
    #     "messages" : ["ejwbnf" , "eninwe"]
    # })

    # app.database.applications.insert_one({
    #     "name": "App1",
    #     "icon": "../images/app-icon.png",
    #     "href": "www.github.com",
    #     "permissions": ["AB", "CD"]
    # })

    print("Connected to MongoDB")

############### user #############################

# Get the details of a user
@app.get("/user-details/{email}", response_model=User)
async def get_user_details(email: str):
    print(f"Received request for user details with email: {email}")
    user = app.database.users.find_one({"email": email})
    if user:
        print(f"User found: {user}")
        return user
    print(f"User not found for email: {email}")
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users", response_model=List[User])
async def get_users():
    users = list(app.database.users.find())
    return [User(id=str(user["_id"]), **user) for user in users]

@app.post("/users")
async def add_user(user: User):
    result = app.database.users.insert_one(user.dict(exclude={"id"}))
    return {"id": str(result.inserted_id)}


@app.put("/users/{user_id}")
async def update_user(user_id: str, user: User):
    result = app.database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.dict(exclude={"id"})}
    )
    if result.modified_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = app.database.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="User not found")

############### levels #############################

@app.get("/permission-levels", response_model=List[PermissionLevel])
async def get_permission_levels():
    levels = list(app.database.permission_levels.find())
    return [PermissionLevel(id=str(level["_id"]), **level) for level in levels]

@app.post("/permission-levels")
async def add_permission_level(level: PermissionLevel):
    result = app.database.permission_levels.insert_one(level.dict(exclude={"id"}))
    return {"id": str(result.inserted_id)}

@app.get("/permission-levels/{level_id}", response_model=PermissionLevel)
async def get_permission_level(level_id: str):
    level = app.database.permission_levels.find_one({"_id": ObjectId(level_id)})
    if level:
        return PermissionLevel(id=str(level["_id"]), **level)
    raise HTTPException(status_code=404, detail="Permission level not found")

@app.put("/permission-levels/{level_id}")
async def update_permission_level(level_id: str, level: PermissionLevel):
    result = app.database.permission_levels.update_one(
        {"_id": ObjectId(level_id)},
        {"$set": level.dict(exclude={"id"})}
    )
    if result.modified_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Permission level not found")

@app.delete("/permission-levels/{level_id}")
async def delete_permission_level(level_id: str):
    result = app.database.permission_levels.delete_one({"_id": ObjectId(level_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Permission level not found")

############### permissions #############################

# permission request for a user
@app.post("/permission-request/{email}", response_model=Dict[str, str])
async def add_permission_request(email: str, permission: PermissionRequest):
    # Check if the user exists
    user = app.database.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_permission = {
        "name": permission.request,
        "urgency": permission.urgency,
        "timeRemaining": permission.timeRemaining,
        "status": "pending"
    }

    # Check if the user already has permissions
    user_permissions = app.database.permissions.find_one({"email": email})

    if user_permissions:
        # Add the new permission to the existing list
        result = app.database.permissions.update_one(
            {"email": email},
            {"$push": {"permissions": new_permission}}
        )
    else:
        # Create a new permissions document for the user
        result = app.database.permissions.insert_one({
            "email": email,
            "permissions": [new_permission]
        })

    if result.modified_count > 0 or result.inserted_id:
        return {"status": "success", "message": "Permission request added successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add permission request")


@app.get("/approved-permissions", response_model=List[Permission])
async def get_approved_permissions():
    permissions = list(app.database.approved_permissions.find())
    return [Permission(id=str(perm["_id"]), **perm) for perm in permissions]

@app.post("/revoke-permission/{permission_id}")
async def revoke_permission(permission_id: str):
    result = app.database.approved_permissions.delete_one({"_id": ObjectId(permission_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Permission not found")

############### applications #############################

# Get the details of all applications
@app.get("/applications", response_model=List[Application])
async def get_applications():
    applications = list(app.database.applications.find())
    return [Application(id=str(app["_id"]), **app) for app in applications]


############### requests #############################

@app.get("/pending-requests", response_model=List[Permission])
async def get_pending_requests():
    requests = list(app.database.pending_requests.find())
    return [Permission(id=str(req["_id"]), **req) for req in requests]

@app.post("/{action}-request/{request_id}")
async def handle_request(action: str, request_id: str, reason: str = None, expiryTime: int = None):
    if action not in ["approve", "deny"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    request = app.database.pending_requests.find_one({"_id": ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if action == "approve":
        app.database.approved_permissions.insert_one({
            "user": request["user"],
            "application": request["application"],
            "expiryDate": expiryTime,
            "reason": reason
        })
    
    app.database.pending_requests.delete_one({"_id": ObjectId(request_id)})
    return {"status": "success"}

############### messages #############################

# return all messages for a user
@app.get("/messages/{email}", response_model=List[str])
async def get_messages(email: str):
    mes = app.database.messages.find_one({"email": email})
    if mes is None:
        raise HTTPException(status_code=404, detail="Messages not found")
    
    # Ensure that `messages` key exists and is a list
    messages = mes.get("messages", [])
    return messages

# return all permissions for a user
@app.get("/permissions/{email}", response_model=List[Permission])
async def get_permissions(email: str):
    print(f"Received request for permissions with email: {email}")
    perm = app.database.permissions.find_one({"email": email})
    if perm is None or "permissions" not in perm:
        raise HTTPException(status_code=404, detail="Permissions not found")
    
    permissions = []
    for p in perm["permissions"]:
        print(p)
        try:
            permission = Permission(**p)
            permissions.append(permission)
        except ValueError as e:
            print(f"Invalid permission data: {p}. Error: {str(e)}")
    
    return permissions

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)