from decouple import Csv, config

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
BLOG_SECRET_KEY = config("BLOG_SECRET_KEY")
BLOG_ALLOWED_HOSTS = config(
    "BLOG_ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)
BLOG_DB_NAME = config("BLOG_DB_NAME", default="blog_api")
BLOG_DB_USER = config("BLOG_DB_USER", default="postgres")
BLOG_DB_PASSWORD = config("BLOG_DB_PASSWORD", default="")
BLOG_DB_HOST = config("BLOG_DB_HOST", default="localhost")
BLOG_DB_PORT = config("BLOG_DB_PORT", default="5432")
BLOG_GITHUB_URL = config(
    "BLOG_GITHUB_URL", default="https://github.com/abdilkakov/blog-api"
)

