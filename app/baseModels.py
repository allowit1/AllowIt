from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# Model for messages of the user(by the email)
class Messages(BaseModel):
    email: str
    messages: List[str]

# Model for permissions 
class Permission(BaseModel):
    id:str
    name: str
    subPermission: Optional[str]
    urgency: str
    status: str
    timeRemaining: Optional[str] = None

# Model for applications
class Application(BaseModel):
    id: Optional[str]
    name: str
    icon: str
    href: str
    permissions: List[str]

# Model for permission requests
class PermissionRequest(BaseModel):
    appName: str
    permissionName: Optional[str] = None
    urgency: str
    timeRemaining: Optional[str] = None

# Model for user
class User(BaseModel):
    name: str
    email: str
    gitHub: str
    permissionLevel: str
    isAdmin: bool

# Model for appPermissions
class AppPermission(BaseModel):
    appName: str
    permissions: List[str]

# Model for permission levels
class PermissionLevel(BaseModel):
    appName: str
    Permissions: List[AppPermission]
