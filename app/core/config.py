import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = "SmartDesk Helpdesk"
    database_url: str = "sqlite:///./smartdesk.db"
    secret_key: str = "change-me"
    session_cookie_name: str = "smartdesk_session"
    session_expiration_minutes: int = 60 * 24
    super_admin_email: str = "olangriffin1@gmail.com"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("SMARTDESK_APP_NAME", cls.app_name),
            database_url=os.getenv("SMARTDESK_DATABASE_URL", cls.database_url),
            secret_key=os.getenv("SMARTDESK_SECRET", cls.secret_key),
            session_cookie_name=os.getenv("SMARTDESK_SESSION_COOKIE_NAME", cls.session_cookie_name),
            session_expiration_minutes=int(
                os.getenv("SMARTDESK_SESSION_EXPIRATION_MINUTES", cls.session_expiration_minutes)
            ),
            super_admin_email=os.getenv("SMARTDESK_SUPER_ADMIN_EMAIL", cls.super_admin_email),
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings.from_env()
