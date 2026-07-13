import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.environ.get('SECRET_KEY', 'placementpro-dev-secret')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'placementpro-dev-jwt-secret')
JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///placementpro.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

CACHE_TYPE = 'RedisCache'
CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/2')
CACHE_DEFAULT_TIMEOUT = 60

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'placementpro@institute.edu')

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@placement.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')

CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
