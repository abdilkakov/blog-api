import os
from pathlib import Path

from decouple import Config, RepositoryEnv

from django.core.asgi import get_asgi_application


ENV_FILE = Path(__file__).resolve().parent / ".env"
if not ENV_FILE.exists():
    raise RuntimeError("Missing settings/.env")

ENV_ID = Config(RepositoryEnv(str(ENV_FILE)))("BLOG_ENV_ID")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")
application = get_asgi_application()
