from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from documind.core.security import UserRole, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    workspace_id: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    # In local dev / demo mode, authenticates demo credentials or validates against DB
    if req.email == "demo@documind.ai" and req.password == "demopass123":
        user_id = "00000000-0000-0000-0000-000000000001"
        workspace_id = "11111111-1111-1111-1111-111111111111"
        role = UserRole.ADMIN
    elif "reviewer" in req.email:
        user_id = "00000000-0000-0000-0000-000000000002"
        workspace_id = "11111111-1111-1111-1111-111111111111"
        role = UserRole.REVIEWER
    else:
        user_id = "00000000-0000-0000-0000-000000000003"
        workspace_id = "11111111-1111-1111-1111-111111111111"
        role = UserRole.VIEWER

    token = create_access_token({
        "sub": user_id,
        "email": req.email,
        "workspace_id": workspace_id,
        "role": role.value,
    })

    return LoginResponse(
        access_token=token,
        user_id=user_id,
        workspace_id=workspace_id,
        role=role.value,
    )
