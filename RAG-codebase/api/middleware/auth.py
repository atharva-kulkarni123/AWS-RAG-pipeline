import os
import logging
import requests
from functools import lru_cache
from jose import jwt, JWTError
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Routes the ALB health check hits — must NEVER require auth
# or ALB will mark the container unhealthy and kill it.
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


@lru_cache(maxsize=1)
def get_jwks(jwks_url: str):
    """
    Fetch Cognito's public keys once and cache them.
    These keys are used to verify every JWT signature.
    """
    response = requests.get(jwks_url, timeout=5)
    response.raise_for_status()
    return response.json()


class CognitoAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        self.user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        self.app_client_id = os.getenv("COGNITO_APP_CLIENT_ID")

        if self.user_pool_id:
            self.jwks_url = (
                f"https://cognito-idp.{self.region}.amazonaws.com"
                f"/{self.user_pool_id}/.well-known/jwks.json"
            )
        else:
            self.jwks_url = None
            logger.warning(
                "COGNITO_USER_POOL_ID not set — auth middleware disabled. "
                "Set it before deploying to production."
            )

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth entirely if Cognito is not configured
        # (useful during local dev / testing)
        if not self.jwks_url:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid Authorization header"
            )

        token = auth_header.split(" ")[1]

        try:
            jwks = get_jwks(self.jwks_url)
            # Decode and verify: signature + expiry + audience
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.app_client_id
            )
            request.state.user_id = claims.get("sub")
            request.state.username = claims.get("cognito:username")
        except JWTError as e:
            logger.warning("jwt_validation_failed", extra={"error": str(e)})
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        except Exception as e:
            logger.error("auth_middleware_error", extra={"error": str(e)})
            raise HTTPException(status_code=500, detail="Auth service error")

        return await call_next(request)