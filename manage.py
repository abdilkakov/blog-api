#!/usr/bin/env python
import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv


ENV_FILE = Path(__file__).resolve().parent / "settings" / ".env"


def main() -> None:
    if not ENV_FILE.is_file():
        raise RuntimeError("Copy settings/.env.example to settings/.env first.")

    environment = Config(RepositoryEnv(str(ENV_FILE)))("BLOG_ENV_ID")
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", f"settings.env.{environment}"
    )

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
