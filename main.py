from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # allows all methods
    allow_headers=["*"],  # allows all headers
)

# Define data models using Pydantic
class Message(BaseModel):
    content: str

class Permission(BaseModel):
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
    time: Optional[int] = None
    days: Optional[int] = None

# Sample data (replace with database in production)
messages = [
    Message(content="Welcome to AllowIt!"),
    Message(content="Your account has been created successfully.")
]

permissions = [
    Permission(name="HR System Access", status="Pending", urgency="High", timeRemaining="(5 days remaining)"),
    Permission(name="Development Server Access", status="Approved", urgency="Medium", timeRemaining="(2 days remaining)"),
    Permission(name="Admin Dashboard", status="Pending", urgency="Low"),
    Permission(name="Finance Data Access", status="Denied", urgency="High")
]

applications = [
    Application(id="app1", name="Application 1", icon="../images/app-icon.png", href="https://github.com/"),
    Application(id="app2", name="Application 2", icon="../images/app-icon.png", href="https://github.com/"),
    Application(id="app3", name="Application 3", icon="../images/app-icon.png", href="https://github.com/"),
    Application(id="app4", name="Application 4", icon="../images/app-icon.png", href="https://github.com/"),
    Application(id="app5", name="Application 5", icon="../images/app-icon.png", href="https://github.com/")
]

# API endpoint to get system messages
@app.get("/messages", response_model=List[Message])
async def get_messages():
    return messages

# API endpoint to get recent permissions
@app.get("/permissions", response_model=List[Permission])
async def get_permissions():
    return permissions

# API endpoint to get available applications
@app.get("/applications", response_model=List[Application])
async def get_applications():
    return applications

# API endpoint to submit a permission request
@app.post("/permission-request")
async def submit_permission_request(request: PermissionRequest):
    # Process the permission request (in production, save to database)
    print(f"Received permission request: {request}")
    # Simulate adding a new permission
    new_permission = Permission(
        name=f"Access to Application {request.applicationId}",
        status="Pending",
        urgency=request.urgency
    )
    permissions.append(new_permission)
    return {"status": "success", "message": "Permission request submitted successfully"}

# Root API endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the AllowIt API"}

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
