import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def database_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(
            BASE_DIR,
            "instance",
            "restaurant.db",
        ),
    ).strip()

    if url.startswith("postgres://"):
        url = url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    elif url.startswith("postgresql://"):
        url = url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return url


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "stonecraft-secret-key",
    )

    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "uploads",
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    LANGUAGES = {
        "th": "ไทย",
        "en": "English",
    }