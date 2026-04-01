#authentication for the api gateway

#JWT create/decode/verify logic
from datetime import datetime, timedelta
#python-jose is the library that handles JWT encoding and decoding. jwt is the object that does the actual work.
#JWTError is the exception it raises when something is wrong with a token.
from jose import JWTError, jwt
#HTTPException: how FastAPI sends an error response back to the client. 
#status is just a collection of named HTTP status codes
from fastapi import HTTPException, status
from pydantic_core import to_json
from app.config import settings

#define the secret key and algorithm for the JWT
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm
    )

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return subject
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )