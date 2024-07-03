# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Optional
# import uvicorn
# import pymongo
# from pymongo import MongoClient
# import os

# # Initialize the FastAPI app
# app = FastAPI()

# # Add CORS middleware to allow cross-origin requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # allows all methods
#     allow_headers=["*"],  # allows all headers
# )

# # Define data models using Pydantic
# class Message(BaseModel):
#     content: str

# class Permission(BaseModel):
#     mail: Optional[str] = None
#     name: str
#     status: str
#     urgency: str
#     timeRemaining: Optional[str] = None

# class Application(BaseModel):
#     id: str
#     name: str
#     icon: str
#     href: str

# class PermissionRequest(BaseModel):
#     applicationId: str
#     reason: Optional[str] = None
#     urgency: str
#     time: Optional[str] = None
#     days: Optional[str] = None

# # Sample data
# messages = [
#     Message(content="Welcome to AllowIt!"),
#     Message(content="Your account has been created successfully.")
# ]

# applications = [
#     Application(id="app1", name="Application 1", icon="../images/app-icon.png", href="https://github.com/"),
#     Application(id="app2", name="Application 2", icon="../images/app-icon.png", href="https://github.com/"),
#     Application(id="app3", name="Application 3", icon="../images/app-icon.png", href="https://github.com/"),
#     Application(id="app4", name="Application 4", icon="../images/app-icon.png", href="https://github.com/"),
#     Application(id="app5", name="Application 5", icon="../images/app-icon.png", href="https://github.com/")
# ]

# company = "AllowIt"
# collection_name = f"pending_{company}"

# MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

# @app.on_event("startup")
# def startup_db_client():
#     app.mongodb_client = MongoClient(MONGO_URL)
#     app.database = app.mongodb_client["allowit123"]
#     app.collection = app.database["permissions"]
#     # Uncomment the following line if you want to insert a test user on every startup
#     # app.database.users.insert_one({"name": "John Doe", "email": "johndoe@gmail.com", "permissions": "HR System Access"})

# # API endpoint to get system messages
# @app.get("/messages/{email}", response_model=List[Message], tags=["messages"])
# async def get_messages(email: str):
#     return messages

# # API endpoint to get recent permissions
# @app.get("/permissions/{email}", response_model=List[Permission])
# async def get_permissions(email: str):
#     try:
#         permissions_cursor = app.database[collection_name].find({"mail": email}, {"_id": 0})
#         permissions_list = list(permissions_cursor)
#         return permissions_list
#     except Exception as e:
#         print(f"Error retrieving permissions: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# # API endpoint to get available applications
# @app.get("/applications", response_model=List[Application])
# async def get_applications(email: Optional[str] = None):
#     return applications

# # API endpoint to submit a permission request
# @app.post("/permission-request")
# async def submit_permission_request(request: PermissionRequest, email: str):
#     try:
#         print(f"Received permission request: {request}")
        
#         new_permission = Permission(
#             mail=email,
#             name=f"Access to Application {request.applicationId}",
#             status="Pending",
#             urgency=request.urgency,
#             timeRemaining=None
#         )

#         app.database[collection_name].insert_one(new_permission.dict())
        
#         return {"status": "success", "message": "Permission request submitted successfully"}
#     except Exception as e:
#         print(f"Error processing permission request: {str(e)}")
#         raise HTTPException(status_code=400, detail=str(e))

# # Root API endpoint
# @app.get("/")
# async def root():
#     return {"message": "Welcome to the AllowIt API"}

# # Run the application
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=5001)


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from pymongo import MongoClient
import os

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models
class Message(BaseModel):
    content: str

class Permission(BaseModel):
    mail: str
    company: Optional[str] = None
    name: str
    status: str
    urgency: str
    timeRemaining: Optional[str] = None

class Application(BaseModel):
    id: str
    name: str
    icon: str
    href: str

class PermissionRequest(BaseModel):
    applicationId: str
    reason: Optional[str] = None
    urgency: str
    time: Optional[str] = None
    days: Optional[str] = None

class UserInfo(BaseModel):
    name: str
    email: str
    phone_number: str
    role: str
    company: str

# MongoDB setup
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://mycluster:123qscesz@allowit.uk1mpor.mongodb.net/?retryWrites=true&w=majority&appName=AllowIt")

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(MONGO_URL)
    app.database = app.mongodb_client["allowit123"]

def get_company_name(email: str) -> str:
    user = app.database.users.find_one({"email": email})
    if user and "company" in user:
        return user["company"]
    raise HTTPException(status_code=404, detail="User or company not found")

@app.get("/user_info/{email}", response_model=UserInfo)
async def get_user_info(email: str):
    user = app.database.users.find_one({"email": email}, {"_id": 0})
    if user:
        return UserInfo(**user)
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/messages/{email}", response_model=List[Message], tags=["messages"])
async def get_messages(email: str):
    # In a real application, you'd fetch messages for this specific user
    return [Message(content="Welcome to AllowIt!"), Message(content="Your account has been created successfully.")]

@app.get("/permissions/{email}", response_model=List[Permission])
async def get_permissions(email: str):
    try:
        company = get_company_name(email)
        print(f"Retrieving permissions for {email} in company {company}")
        all_permissions = []
        for status in ["pending", "approved", "denied"]:
            collection_name = f"{status}_{company}"
            permissions_cursor = app.database[collection_name].find({"mail": email}, {"_id": 0})
            all_permissions.extend(list(permissions_cursor))
        return all_permissions
    except Exception as e:
        print(f"Error retrieving permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/applications", response_model=List[Application])
async def get_applications(email: str):
    # In a real application, you might filter applications based on user permissions
    return [
        Application(id="app1", name="Application 1", icon="../images/app-icon.png", href="https://github.com/"),
        Application(id="app2", name="Application 2", icon="../images/app-icon.png", href="https://github.com/"),
        Application(id="app3", name="Application 3", icon="../images/app-icon.png", href="https://github.com/"),
        Application(id="app4", name="Application 4", icon="../images/app-icon.png", href="https://github.com/"),
        Application(id="app5", name="Application 5", icon="../images/app-icon.png", href="https://github.com/")
    ]

@app.post("/permission-request")
async def submit_permission_request(request: PermissionRequest, email: str):
    try:
        company = get_company_name(email)
        new_permission = Permission(
            mail=email,
            company=get_company_name(email),
            name=f"Access to Application {request.applicationId}",
            urgency=request.urgency,
            timeRemaining=None
        )
        collection_name = f"pending_{company}"
        app.database[collection_name].insert_one(new_permission.dict())
        return {"status": "success", "message": "Permission request submitted successfully"}
    except Exception as e:
        print(f"Error processing permission request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the AllowIt API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)