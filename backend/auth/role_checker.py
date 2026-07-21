# # backend/auth/role_checker.py
# from typing import List
# from fastapi import HTTPException, Depends, status
# from auth.jwt_handler import verify_token
# from fastapi.security import OAuth2PasswordBearer

# # This looks for the 'Authorization: Bearer <token>' header
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# class RoleChecker:
#     def __init__(self, allowed_roles: List[str]):
#         self.allowed_roles = allowed_roles

#     def __call__(self, token: str = Depends(oauth2_scheme)):
#         payload = verify_token(token)
#         user_role = payload.get("role")
        
#         if user_role not in self.allowed_roles:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"Role '{user_role}' is not authorized to access this resource."
#             )
#         return payload # Returns user data to the route if successful

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import decode_token

security = HTTPBearer()

class RoleChecker:
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):

        token = credentials.credentials

        payload = decode_token(token)

        role = payload.get("role")

        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return payload