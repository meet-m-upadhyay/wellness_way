"""
Authentication service for JWT and Google OAuth integration
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import time

from jose import JWTError, jwt
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth import exceptions as google_exceptions
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.user import User, RegistrationRequest
from app.schemas.user import UserProfileCreate, UserProfileResponse


class AuthService:
    """Authentication service for JWT and Google OAuth"""
    
    def __init__(self):
        self.settings = get_settings()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = self.settings.security.access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.security.refresh_token_expire_days
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.get_jwt_secret_key(), 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.get_jwt_secret_key(), 
            algorithm=self.algorithm
        )
        return encoded_jwt

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token, 
                self.settings.get_jwt_secret_key(), 
                algorithms=[self.algorithm]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def verify_google_token(self, token: str) -> Dict[str, Any]:
        """Verify Google OAuth token and return user info"""
        try:
            # First attempt with clock skew tolerance
            try:
                idinfo = id_token.verify_oauth2_token(
                    token, 
                    requests.Request(), 
                    self.settings.security.google_client_id,
                    clock_skew_in_seconds=60  # Allow 60 seconds of clock skew
                )
            except ValueError as e:
                # If clock skew error, try with even more tolerance
                if "Token used too early" in str(e) or "Token used too late" in str(e):
                    print(f"Clock skew detected, retrying with more tolerance: {e}")
                    idinfo = id_token.verify_oauth2_token(
                        token, 
                        requests.Request(), 
                        self.settings.security.google_client_id,
                        clock_skew_in_seconds=300  # Allow 5 minutes of clock skew
                    )
                else:
                    raise
            
            # Check if the token is for our app
            if idinfo['aud'] != self.settings.security.google_client_id:
                raise ValueError('Wrong audience.')
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }
            
        except ValueError as e:
            error_msg = str(e)
            # Provide more helpful error messages for common issues
            if "Token used too early" in error_msg:
                error_msg = "Clock synchronization issue. Please check your system time or try again in a few moments."
            elif "Token used too late" in error_msg:
                error_msg = "Token has expired. Please try logging in again."
            elif "Wrong audience" in error_msg:
                error_msg = "Invalid token audience. Please ensure you're using the correct Google OAuth configuration."
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {error_msg}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )
    
    def get_or_create_user_from_google(
        self, 
        google_user_info: Dict[str, Any], 
        db: Session
    ) -> tuple[User, bool]:
        """Get existing user or create registration request from Google OAuth info
        
        Returns:
            tuple: (User or None, is_new_registration)
        """
        
        # Define admin email
        ADMIN_EMAIL = "meetupadhyaykgp@gmail.com"
        
        # Try to find user by Google ID first
        user = db.query(User).filter(User.google_id == google_user_info['google_id']).first()
        
        if user:
            # Update user info if needed
            if user.email != google_user_info['email']:
                user.email = google_user_info['email']
            if user.name != google_user_info['name'] and google_user_info['name']:
                user.name = google_user_info['name']
            
            # Set admin status based on email
            user.is_admin = (user.email == ADMIN_EMAIL)
            
            # IMPORTANT: Do NOT override is_active - respect admin disable decisions
            # Only set is_active = True for new users or if they're admin
            if user.is_admin:
                user.is_active = True  # Admins are always active
            # For non-admin users, keep their current is_active status (don't override admin disable)
            
            db.commit()
            db.refresh(user)
            return user, False
        
        # Try to find user by email
        user = db.query(User).filter(User.email == google_user_info['email']).first()
        
        if user:
            # Link Google account to existing user
            user.google_id = google_user_info['google_id']
            user.is_admin = (user.email == ADMIN_EMAIL)
            
            # IMPORTANT: Do NOT override is_active - respect admin disable decisions
            # Only set is_active = True for new users or if they're admin
            if user.is_admin:
                user.is_active = True  # Admins are always active
            # For non-admin users, keep their current is_active status (don't override admin disable)
            
            db.commit()
            db.refresh(user)
            return user, False
        
        # For admin email, create user directly (no approval needed)
        if google_user_info['email'] == ADMIN_EMAIL:
            new_user = User(
                id=uuid.uuid4(),
                email=google_user_info['email'],
                google_id=google_user_info['google_id'],
                name=google_user_info['name'] or 'User',
                is_active=True,
                is_admin=True,
                approval_status='approved',
                profile_completed=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return new_user, False
        
        # For non-admin users, check if there's already a pending registration request
        existing_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.email == google_user_info['email']
        ).first()
        
        if existing_request:
            if existing_request.status == 'approved':
                # Create the user since they've been approved
                new_user = User(
                    id=uuid.uuid4(),
                    email=google_user_info['email'],
                    google_id=google_user_info['google_id'],
                    name=google_user_info['name'] or existing_request.name,
                    is_active=True,
                    is_admin=False,
                    approval_status='approved',
                    profile_completed=False
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                return new_user, False
            elif existing_request.status == 'pending':
                # Return None to indicate pending approval
                return None, False
            elif existing_request.status == 'declined':
                # Allow them to create a new request
                existing_request.status = 'pending'
                existing_request.name = google_user_info['name'] or existing_request.name
                existing_request.google_id = google_user_info['google_id']
                db.commit()
                return None, True
        else:
            # Create new registration request
            new_request = RegistrationRequest(
                id=uuid.uuid4(),
                email=google_user_info['email'],
                name=google_user_info['name'] or 'User',
                google_id=google_user_info['google_id'],
                status='pending'
            )
            
            db.add(new_request)
            db.commit()
            db.refresh(new_request)
            
            return None, True
    
    def get_user_by_id(self, user_id: str, db: Session) -> Optional[User]:
        """Get user by ID (regardless of active status for token verification)"""
        try:
            user_uuid = uuid.UUID(user_id)
            return db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            return None

    def get_user_by_email(self, email: str, db: Session) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    def authenticate_user(self, email: str, password: str, db: Session) -> User:
        """Authenticate a user with email and password"""
        user = self.get_user_by_email(email, db)
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        if not self.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        return user
    
    def create_tokens_for_user(self, user: User) -> Dict[str, str]:
        """Create access and refresh tokens for user"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def refresh_access_token(self, refresh_token: str, db: Session) -> Dict[str, str]:
        """Create new access token from refresh token"""
        payload = self.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = self.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return self.create_tokens_for_user(user)
    
    def get_registration_request_by_email(self, email: str, db: Session) -> Optional[RegistrationRequest]:
        """Get registration request by email"""
        return db.query(RegistrationRequest).filter(RegistrationRequest.email == email).first()
    
    def get_user_status(self, email: str, db: Session) -> Dict[str, Any]:
        """Get user approval status"""
        # Check if user exists and is approved
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {
                "status": user.approval_status,
                "message": "User is approved and can access the application" if user.approval_status == 'approved' else f"User status: {user.approval_status}"
            }
        
        # Check registration request
        request = self.get_registration_request_by_email(email, db)
        if request:
            if request.status == 'pending':
                return {
                    "status": "pending",
                    "message": "Your registration is pending admin approval. You will receive an email once approved."
                }
            elif request.status == 'declined':
                return {
                    "status": "declined", 
                    "message": "Your registration request was declined. You can try registering again."
                }
        
        return {
            "status": "not_found",
            "message": "No registration found. Please sign in to create a registration request."
        }


# Global auth service instance
auth_service = AuthService()