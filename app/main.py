from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pymongo import MongoClient
import os
from bson import ObjectId
from baseModels import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

# Global database connection
mongodb_client = None
database = None

def get_database():
    global mongodb_client, database
    if mongodb_client is None:
        mongodb_client = MongoClient(MONGO_URL)
        database = mongodb_client["allowit123"]
    return database

@app.on_event("startup")
async def startup_db_client():
    global mongodb_client, database
    mongodb_client = MongoClient(MONGO_URL)
    database = mongodb_client["allowit123"]
    print("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_db_client():
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()

#region user

# Get user details by email
@app.get("/user-details/{email}", response_model=User)
async def get_user_details(email: str):
    db = get_database()
    user = db.users.find_one({"email": email})
    if user:
        user['id'] = str(user['_id'])
        return user
    raise HTTPException(status_code=404, detail="User not found")

# Get all users
@app.get("/users", response_model=List[User])
async def get_users():
    db = get_database()
    users = list(db.users.find())
    for user in users:
        user['id'] = str(user['_id'])
    return users

# Update user details
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    db = get_database()
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.dict(exclude_unset=True)}
    )
    if result.modified_count:
        updated_user = db.users.find_one({"_id": ObjectId(user_id)})
        if updated_user:
            updated_user['id'] = str(updated_user['_id'])
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

# Delete user
@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    db = get_database()
    result = db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="User not found")


# Add user
@app.post ("/users" , response_model=User)
async def add_user(user_data: dict):
    
    db = get_database()
    name = user_data['name']
    email = user_data['email']

    if 'gitHub' in user_data:
        gitHub = user_data['gitHub']
    else:
        gitHub = None

    permissionLevel = user_data['permissionLevel']
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = User(
        name=name,
        email=email,
        gitHub=gitHub,
        permissionLevel=permissionLevel,
        isAdmin=False
    )

    result = db.users.insert_one(new_user.dict())
    if result.inserted_id:
        return new_user
    else:
        raise HTTPException(status_code=500, detail="Failed to add user")

#endregion


#region permissions-levels  

# Get all permission levels
@app.get("/permission-levels", response_model=List[PermissionLevel])
async def get_permission_levels():
    db = get_database()
    levels = list(db.permission_levels.find())
    return [PermissionLevel(id=str(level['_id']), appName=level['appName'], Permissions=level['Permissions']) for level in levels]


# add permission level
@app.post("/permission-levels", response_model=PermissionLevel)
async def add_permission_level(level_data: dict):
    print("Received data:", level_data)
    db = get_database()
    
    appName = level_data['appName']
    permissions = level_data['permissions']

    existing_level = db.permission_levels.find_one({"appName": appName})
    if existing_level:
        raise HTTPException(status_code=400, detail="Permission level already exists")

    app_permissions = []
    for app_id, perms in permissions.items():
        app = db.applications.find_one({"_id": ObjectId(app_id)})
        if app:
            app_permissions.append(AppPermission(
                appName=app['appName'],
                permissions=perms
            ))

    new_level = PermissionLevel(
        appName=appName,
        Permissions=app_permissions
    )

    db.permission_levels.insert_one(new_level.dict())

    return new_level

# Update permission level
@app.put("/permission-levels/{level_id}", response_model=PermissionLevel)
async def update_permission_level(level_id: str, level_data: dict):
    db = get_database()
    appName = level_data['appName']
    permissions = level_data['permissions']

    existing_level = db.permission_levels.find_one({"_id": ObjectId(level_id)})
    if not existing_level:
        raise HTTPException(status_code=404, detail="Permission level not found")
    
    app_permissions = []
    for app_id, perms in permissions.items():
        app = db.applications.find_one({"_id": ObjectId(app_id)})
        if app:
            app_permissions.append(AppPermission(
                appName=app['appName'],
                permissions=perms
            ))

    updated_level = PermissionLevel(
        id=level_id,
        appName=appName,
        Permissions=app_permissions
    )

    result = db.permission_levels.update_one(
        {"_id": ObjectId(level_id)},
        {"$set": updated_level.dict(exclude={'id'})}
    )
    
    if result.modified_count:
        return updated_level
    else:
        raise HTTPException(status_code=500, detail="Failed to update permission level")

# Delete permission level
@app.delete("/permission-levels/{level_id}")
async def delete_permission_level(level_id: str):
    db = get_database()
    result = db.permission_levels.delete_one({"_id": ObjectId(level_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Permission level not found")

#endregion

#region requests

# Add permission request
@app.post("/permission-request/{email}", response_model=Dict[str, str])
async def add_permission_request(email: str, permission: Permission):
    try:
        db = get_database()
        user = db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_permission = permission.dict()
        new_permission["email"] = email
        new_permission["status"] = "pending"

        result = db.permissions.insert_one(new_permission)

        if result.inserted_id:
            return {"status": "success", "message": "Permission request added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add permission request")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# Get all pending requests
@app.get("/pending-requests", response_model=List[Permission])
async def get_pending_requests():
    db = get_database()
    all_permissions = list(db.permissions.find())
    pending_requests = []
    #TODO:add sql to filter
    for permission in all_permissions:
        if permission['status'] == 'pending':
            pending_requests.append(permission)

    return pending_requests

#TODO: change the reason to be sent into messages table, and fux the code\
# Handle request
@app.post("/{action}-request/{request_id}")
async def handle_request(action: str, request_id: str, reason: str = None, expiryTime: int = None):
    try:
        db = get_database()

        if action not in ["approve", "deny"]: # if action is not approve or deny raise an error
            raise HTTPException(status_code=400, detail="Invalid action")
        
        user_permission = db.permissions.find_one({"_id": ObjectId(request_id)}) # find the request by id
        if not user_permission: # if request not found raise an error
            raise HTTPException(status_code=404, detail="Error in finding request")
        

        user_permission['status'] = 'approved' if action == 'approve' else 'denied'
        if expiryTime:
            user_permission['timeRemaining'] = f"{expiryTime} hours"
            #TODO: add expiry time to the request
        
        if reason:
            db.messages.update_one(
                {"email": user_permission['email']},
                {"$push": {"messages": reason}}
            )
        
        result = db.permissions.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": user_permission}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update request")


# Get all approved permissions
@app.get("/approved-permissions", response_model=List[Permission])
async def get_approved_permissions():
    db = get_database()
    all_permissions = list(db.permissions.find())
    approved_permissions = []
    for permission in all_permissions:
        if permission['status'] == 'approved':
            approved_permissions.append(permission)

    return approved_permissions

# Revoke permission
@app.post("/revoke-permission/{permission_id}")
async def revoke_permission(permission_id: str):
    try:
        db = get_database()
        user_permissions = db.permissions.find_one({"_id": ObjectId(permission_id)})

        if not user_permissions:
            raise HTTPException(status_code=404, detail="Permission not found")
        

        user_permissions['status'] = 'revoked'
        
        result = db.permissions.update_one(
            {"_id": ObjectId(permission_id)},
            {"$set": {"permissions": user_permissions['permissions']}}
        )
        
        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to revoke permission")

#endregion

#region applications

# Get all applications
@app.get("/applications", response_model=List[Application])
async def get_applications():
    db = get_database()
    applications = list(db.applications.find())
    return applications

# Get application by name
@app.get("/application/{name}", response_model=Application)
async def get_application(name: str):
    db = get_database()
    app = db.applications.find_one({"name": name})
    if app:
        return app
    raise HTTPException(status_code=404, detail="Application not found")

#endregion

#region messages
    
@app.get("/messages/{email}", response_model=List[str])
async def get_messages(email: str):
    db = get_database()
    mes = db.messages.find_one({"email": email})
    if mes is None:
        raise HTTPException(status_code=404, detail="Messages not found")
    return mes.get("messages", [])

#endregion

#region permissions

from fastapi import FastAPI, HTTPException
from typing import List
from bson import ObjectId

@app.get("/permissions/{email}", response_model=List[Permission])
async def get_permissions(email: str):
    db = get_database()
    permissions = list(db.permissions.find({"email": email}))
    
    if not permissions:
        raise HTTPException(status_code=404, detail="Permissions not found")
    
    # Convert ObjectId to string for each permission
    for perm in permissions:
        perm['id'] = str(perm['_id'])
        del perm['_id']
    
    return permissions

#endregion


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
