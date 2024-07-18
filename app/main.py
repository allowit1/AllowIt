from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uvicorn
from pymongo import MongoClient
import os
from bson import ObjectId
import sched
import random
import time
from datetime import datetime, timedelta

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
    
#     document = {
#     "email": "inefi@gmail.com",
#     "permissions": [
#         {
#             "name": "Camera",
#             "subPermission": "Camera",
#             "urgency": "High",
#             "status": "pending",
#             "timeRemaining": "1 minute"  # Fixed syntax issue
#         }
#     ]
# }
    
#     database.permissions.insert_one( document )


@app.on_event("shutdown")
async def shutdown_db_client():
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()

class Messages(BaseModel):
    email: str
    messages: List[str]

class Permission(BaseModel):
    id:str
    name: str
    subPermission: Optional[str] = None
    urgency: str
    status: str
    timeRemaining: Optional[str] = None

class Application(BaseModel):
    id: str
    name: str
    icon: str
    href: str
    permissions: List[str]

class PermissionRequest(BaseModel):
    subId: Optional[int] = None
    request: str
    subPermission: Optional[str] = None
    urgency: str
    timeRemaining: Optional[str] = None

class User(BaseModel):
    name: str
    email: str
    phone: str
    permissionLevel: str
    isAdmin: bool


class AppPermission(BaseModel):
    name: str
    permissions: List[str]

class PermissionLevel(BaseModel):
    name: str
    Permissions: List[AppPermission]


@app.get("/user-details/{email}", response_model=User)
async def get_user_details(email: str):
    db = get_database()
    user = db.users.find_one({"email": email})
    if user:
        user['id'] = str(user['_id'])
        return user
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users", response_model=List[User])
async def get_users():
    db = get_database()
    users = list(db.users.find())
    for user in users:
        user['id'] = str(user['_id'])
    return users


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


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    db = get_database()
    result = db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="User not found")

  
@app.get("/permission-levels", response_model=List[PermissionLevel])
async def get_permission_levels():
    db = get_database()
    levels = list(db.permission_levels.find())
    return [PermissionLevel(id=str(level['_id']), name=level['name'], Permissions=level['Permissions']) for level in levels]


@app.post("/permission-levels", response_model=PermissionLevel)
async def add_permission_level(level_data: dict):
    db = get_database()
    name = level_data['name']
    permissions = level_data['permissions']

    existing_level = db.permission_levels.find_one({"name": name})
    if existing_level:
        raise HTTPException(status_code=400, detail="Permission level already exists")

    app_permissions = []
    for app_id, perms in permissions.items():
        app = db.applications.find_one({"_id": ObjectId(app_id)})
        if app:
            app_permissions.append(AppPermission(
                name=app['name'],
                permissions=perms
            ))

    new_level = PermissionLevel(
        name=name,
        Permissions=app_permissions
    )

    result = db.permission_levels.insert_one(new_level.dict())

    if result.inserted_id:
        return new_level
    else:
       database.permission_level.insert_one(level)
    raise HTTPException(status_code=500, detail="Failed to add permission level")

@app.put("/permission-levels/{level_id}", response_model=PermissionLevel)
async def update_permission_level(level_id: str, level_data: dict):
    db = get_database()
    name = level_data['name']
    permissions = level_data['permissions']

    existing_level = db.permission_levels.find_one({"_id": ObjectId(level_id)})
    if not existing_level:
        raise HTTPException(status_code=404, detail="Permission level not found")
    
    app_permissions = []
    for app_id, perms in permissions.items():
        app = db.applications.find_one({"_id": ObjectId(app_id)})
        if app:
            app_permissions.append(AppPermission(
                name=app['name'],
                permissions=perms
            ))

    updated_level = PermissionLevel(
        id=level_id,
        name=name,
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

@app.delete("/permission-levels/{level_id}")
async def delete_permission_level(level_id: str):
    db = get_database()
    result = db.permission_levels.delete_one({"_id": ObjectId(level_id)})
    if result.deleted_count:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Permission level not found")

@app.post("/permission-request/{email}", response_model=Dict[str, str])
async def add_permission_request(email: str, permission: PermissionRequest):
    try:
        db = get_database()
        user = db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        new_permission = {
            "name": permission.request,
            "subId":random.randint(1,1000),
            "subPermission": permission.subPermission,
            "urgency": permission.urgency,
            "timeRemaining": permission.timeRemaining,
            "status": "pending"
        }

        user_permissions = db.permissions.find_one({"email": email})

        if user_permissions:
            result = db.permissions.update_one(
                {"email": email},
                {"$push": {"permissions": new_permission}}
            )
        else:
            result = db.permissions.insert_one({
                "email": email,
                "permissions": [new_permission]
            })

        return {"status": "success", "message": "Permission request added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add permission request")

@app.get("/pending-requests", response_model=List[Permission])
async def get_pending_requests():
    db = get_database()
    all_permissions = list(db.permissions.find())
    pending_requests = []
    for user_permissions in all_permissions:
        for permission in user_permissions['permissions']:
            if permission['status'] == 'pending':
                pending_requests.append(permission)
    return pending_requests

scheduler = sched.scheduler(time.time, time.sleep)


@app.post("/{action}-request/{request_id}")
async def handle_request(action: str, request_id: str, reason: str = None, expiryTime: int = None):
    db = get_database()

    if action not in ["approve", "deny"]: # if action is not approve or deny raise an error
        raise HTTPException(status_code=400, detail="Invalid action")
    
    user_permissions = db.permissions.find_one({"_id": ObjectId(request_id)}) # find the request by id
    if not user_permissions: # if request not found raise an error
        raise HTTPException(status_code=404, detail="Request not found")
    
    for permission in user_permissions['permissions']: # loop through all permissions and update the status
        if permission['status'] == 'pending':
            if action == "approve":
                permission['status'] = 'approved'
            elif action == "deny":
                permission['status'] = 'denied'
            if expiryTime:
                permission['timeRemaining'] = f"{expiryTime} hours"
    
    revocation_time = datetime.now() + timedelta(minutes=expiryTime) if expiryTime else None
    scheduler.enterabs(revocation_time.timestamp(), 1, revoke_permission, (request_id,)) # schedule the revocation of the permission
    ###########################################################################################################
    result = db.permissions.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"permissions": user_permissions['permissions']}}
    )

    if result.modified_count:
        user = db.messages.find_one({"email": user_permissions['email']})
        message = f"Your request for {user_permissions['permissions'][0]['name']} has been {action}ed"
        if not user:
            db.messages.insert_one({"email": user_permissions['email'], "messages": [message]})
        else:
            db.messages.update_one({"email": user_permissions['email']}, {"$push": {"messages": message}})
     
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to update request")

@app.get("/approved-permissions", response_model=List[Permission])
async def get_approved_permissions():
    '''
    Get all approved permissions
    '''
    db = get_database()
    all_permissions = list(db.permissions.find())
    approved_permissions = []
    for user_permissions in all_permissions:
        for permission in user_permissions['permissions']:
            if permission['status'] == 'approved':
                approved_permissions.append(permission)
    return approved_permissions

@app.post("/revoke-permission/{permission_id}")
async def revoke_permission(permission_id: str):
    db = get_database()
    user_permissions = db.permissions.find_one({"_id": ObjectId(permission_id)})
    if not user_permissions:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    for permission in user_permissions['permissions']:
        if permission['status'] == 'approved':
            permission['status'] = 'revoked'
    
    result = db.permissions.update_one(
        {"_id": ObjectId(permission_id)},
        {"$set": {"permissions": user_permissions['permissions']}}
    )
    
    if result.modified_count:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to revoke permission")

@app.get("/applications", response_model=List[Application])
async def get_applications():
    db = get_database()
    applications = list(db.applications.find())
    for app in applications:
        app['id'] = str(app['_id'])
    return applications

@app.get("/application/{name}", response_model=Application)
async def get_application(name: str):
    db = get_database()
    app = db.applications.find_one({"name": name})
    if app:
        app['id'] = str(app['_id'])
        return app
    raise HTTPException(status_code=404, detail="Application not found")

@app.get("/messages/{email}", response_model=List[str])
async def get_messages(email: str):
    db = get_database()
    mes = db.messages.find_one({"email": email})
    if mes is None:
        raise HTTPException(status_code=404, detail="Messages not found")
    return mes.get("messages", [])

@app.get("/permissions/{email}", response_model=List[Permission])
async def get_permissions(email: str):
    db = get_database()
    perm = db.permissions.find_one({"email": email})
    if perm is None or "permissions" not in perm:
        raise HTTPException(status_code=404, detail="Permissions not found")
    all_permissions = []
    for permission in perm['permissions']:
        permission['id'] = str(permission['_id']) if '_id' in permission else str(perm['_id'])
        if 'reason' in permission:
            del permission['reason']
        all_permissions.append(permission)
    return all_permissions
    

@app.post ("/users" , response_model=User)
async def add_user(user_data: dict):
    
    db = get_database()
    name = user_data['name']
    email = user_data['email']
    phone = user_data['phone']
    permissionLevel = user_data['permissionLevel']
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = User(
        name=name,
        email=email,
        phone=phone,
        permissionLevel=permissionLevel,
        isAdmin=False
    )
    result = db.users.insert_one(new_user.dict())
    if result.inserted_id:
        return new_user
    else:
        raise HTTPException(status_code=500, detail="Failed to add user")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)