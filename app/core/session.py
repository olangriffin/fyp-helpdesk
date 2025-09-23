from fastapi import Response

from app.core.config import get_settings

settings = get_settings()


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_expiration_minutes * 60,
        httponly=True,
        secure=False,
        samesite="lax",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name)
