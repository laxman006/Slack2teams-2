# -*- coding: utf-8 -*-
"""
Authentication and Authorization Module

Implements OAuth2 security using FastAPI's dependency injection pattern.
Validates Microsoft OAuth tokens and enforces access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from typing import Optional, Dict
import logging

# Configure logging
logger = logging.getLogger(__name__)

# OAuth2 Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    Validate Microsoft OAuth access token and return authenticated user information.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        Dictionary containing user_id, email, and name
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    access_token = credentials.credentials
    
    try:
        # Verify token with Microsoft Graph API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            
            if response.status_code == 401:
                logger.warning("Invalid or expired access token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if response.status_code != 200:
                logger.error(f"Microsoft Graph API error: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to verify access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_info = response.json()
            
            # Extract user information
            user_id = user_info.get("id")
            user_email = user_info.get("mail") or user_info.get("userPrincipalName", "")
            user_name = user_info.get("displayName", "User")
            
            if not user_id:
                logger.error("No user ID in Microsoft Graph response")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user information",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Validate CloudFuze email domain
            if not user_email.endswith("@cloudfuze.com"):
                logger.warning(f"Access denied for non-CloudFuze email: {user_email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Only CloudFuze company accounts are allowed.",
                )
            
            logger.info(f"User authenticated successfully: {user_id} ({user_email})")
            
            return {
                "id": user_id,
                "email": user_email,
                "name": user_name
            }
            
    except httpx.RequestError as e:
        logger.error(f"Network error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


async def verify_user_access(
    user_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify that the authenticated user has access to the requested user resource.
    Prevents IDOR by ensuring user_id matches the authenticated user's ID.
    
    Args:
        user_id: The user_id from the URL path parameter
        current_user: The authenticated user from get_current_user dependency
        
    Returns:
        The current_user dictionary if access is allowed
        
    Raises:
        HTTPException: 403 if the user tries to access another user's resources
    """
    if current_user["id"] != user_id:
        logger.warning(
            f"Access denied: User {current_user['id']} attempted to access "
            f"resources belonging to user {user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own resources.",
        )
    
    return current_user


async def require_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify that the authenticated user has administrative privileges.
    Currently, all CloudFuze email users are considered admins for internal tools.
    
    Args:
        current_user: The authenticated user from get_current_user dependency
        
    Returns:
        The current_user dictionary if user is an admin
        
    Raises:
        HTTPException: 403 if the user is not an admin
    """
    # For now, all CloudFuze users have admin access to these endpoints
    # In the future, you could check a specific admin list or database
    if not current_user["email"].endswith("@cloudfuze.com"):
        logger.warning(
            f"Admin access denied for user {current_user['id']} ({current_user['email']})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    
    logger.info(f"Admin access granted to {current_user['id']} ({current_user['email']})")
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, str]]:
    """
    Optional authentication - returns user if token is provided, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional bearer token from Authorization header
        
    Returns:
        User dictionary if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        # Create a new credentials object to pass to get_current_user
        return await get_current_user(credentials)
    except HTTPException:
        # If authentication fails, return None instead of raising exception
        return None

