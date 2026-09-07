from datetime import datetime, timedelta, timezone
import os

import jwt
from dotenv import load_dotenv


load_dotenv()


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)


def create_access_token(
    user_id: int
) -> str:
    """
    Create a JWT access token for a user.
    """

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def decode_access_token(
    token: str
) -> int | None:
    """
    Decode and validate a JWT access token.

    Returns the user ID if valid.
    Returns None if the token is invalid or expired.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError
    ):
        return None