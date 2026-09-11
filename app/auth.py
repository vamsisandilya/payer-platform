import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_identity(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


class RequireRole:
    def __init__(self, role: str):
        self.role = role

    def __call__(self, identity: dict = Depends(get_current_identity)) -> dict:
        if identity["role"] != self.role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return identity
