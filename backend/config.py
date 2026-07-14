import os
from dotenv import load_dotenv

# Absolute path to the backend directory, used to locate the .env file.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Loads backend/.env into the process environment.
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Flask session/CSRF signing key and JWT signing key.
SECRET_KEY = os.environ.get('SECRET_KEY', 'placementpro-dev-secret')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'placementpro-dev-jwt-secret')
# Access tokens expire after 8 hours.
JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8

# Database connection string; defaults to a local SQLite file.
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///placementpro.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Caching backend and default per-key expiry, in seconds.
CACHE_TYPE = 'RedisCache'
CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/2')
CACHE_DEFAULT_TIMEOUT = 60

# Celery broker (task queue) and result backend, both backed by Redis.
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# SMTP settings used by Flask-Mail for outgoing notification emails.
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'placementpro@placement.com')

# Credentials used to seed the single admin account on first startup.
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@placement.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')

# Origins allowed to make cross-origin requests to the API.
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
