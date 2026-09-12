"""
Django settings for ecommerce project.
Environment-driven version, ready for local dev and production deployment.
"""

from pathlib import Path
import environ

# ------------------------------
# BASE DIRECTORY
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# ENVIRONMENT VARIABLES
# ------------------------------
# Reads a .env file in the project root if present (local dev).
# In production, set these as real environment variables in your host's dashboard.
env = environ.Env(
    DEBUG=(bool, False),
)
env.read_env(BASE_DIR / '.env')

# ------------------------------
# SECURITY
# ------------------------------
SECRET_KEY = env('SECRET_KEY')  # no default on purpose — app should fail to start without one
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ------------------------------
# INSTALLED APPS
# ------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'corsheaders',

    # Your apps
    'shop',
]

# ------------------------------
# MIDDLEWARE
# ------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serves static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

# ------------------------------
# URL CONFIGURATION
# ------------------------------
ROOT_URLCONF = 'ecommerce.urls'

# ------------------------------
# TEMPLATES
# ------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ------------------------------
# WSGI APPLICATION
# ------------------------------
WSGI_APPLICATION = 'ecommerce.wsgi.application'

# ------------------------------
# DATABASE
# ------------------------------
# Falls back to local SQLite if DATABASE_URL isn't set, so local dev still
# works with zero config. In production, set DATABASE_URL to your Postgres
# connection string (Railway/Render provide this automatically).
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}

# ------------------------------
# TIMEZONE
# ------------------------------
TIME_ZONE = 'Asia/Manila'
USE_TZ = True

# ------------------------------
# PASSWORD VALIDATORS
# ------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------
# INTERNATIONALIZATION
# ------------------------------
LANGUAGE_CODE = 'en-us'
USE_I18N = True

# ------------------------------
# STATIC FILES (served via WhiteNoise in production)
# ------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ------------------------------
# MEDIA FILES (user-uploaded product images)
# ------------------------------
# NOTE: most hosts (Railway/Render free tiers) wipe local disk on every
# deploy/restart. This works for a quick demo, but if product images need
# to survive redeploys, swap this for django-storages + S3/Cloudinary later.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------------------
# DEFAULT PRIMARY KEY
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------
# AUTH REDIRECTS
# ------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/shop/'
LOGOUT_REDIRECT_URL = '/shop/'

# ------------------------------
# SESSION SETTINGS
# ------------------------------
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True

# ------------------------------
# PRODUCTION-ONLY SECURITY HARDENING
# ------------------------------
# These only kick in when DEBUG=False, so local development is unaffected.
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
