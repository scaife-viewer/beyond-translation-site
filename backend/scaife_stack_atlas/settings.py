import os


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = PACKAGE_ROOT

DEBUG = bool(int(os.environ.get("DEBUG", "1")))

ALLOWED_HOSTS = ["localhost"]
if "HEROKU_APP_NAME" in os.environ:
    ALLOWED_HOSTS = ["*"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "UTC"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = int(os.environ.get("SITE_ID", 1))

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = "/site_media/media/"

# Absolute path to the directory static files should be collected to.
# Don"t put anything in this directory yourself; store your static files
# in apps" "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATIC_ASSET_ROOT = os.path.join(PROJECT_ROOT, "static")

STATICFILES_DIRS = [STATIC_ASSET_ROOT]

WHITENOISE_ROOT = STATIC_ASSET_ROOT

#  Secret key
if DEBUG:
    SECRET_KEY = "3#l*7k&+=w-z7uc@^78#w*3(u44%sgyt4#d2lye#7_98qk5j_n"
else:
    # Will raise a KeyError if SECRET_KEY env var is not defined
    SECRET_KEY = os.environ["SECRET_KEY"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PACKAGE_ROOT, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "scaife_stack_atlas.context_processors.settings",
            ],
        },
    }
]

MIDDLEWARE = [
    "querycount.middleware.QueryCountMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "scaife_stack_atlas.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "scaife_stack_atlas.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sites",
    # override runserver static handling
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # third party
    "corsheaders",
    "django_extensions",
    "django_jsonfield_backport",
    "graphene_django",
    "treebeard",
    # scaife_viewer
    "scaife_viewer.atlas",
    # project
    "scaife_stack_atlas",
]

ADMIN_URL = "admin:index"
CONTACT_EMAIL = "support@example.com"

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        }
    },
}

FIXTURE_DIRS = [os.path.join(PROJECT_ROOT, "fixtures")]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CORS_ORIGIN_ALLOW_ALL = True

GRAPHENE = {
    "SCHEMA": "scaife_stack_atlas.schema.schema",
    # setting RELAY_CONNECTION_MAX_LIMIT to None removes the limit; for backwards compatability with current API
    # @@@ restore the limit
    "RELAY_CONNECTION_MAX_LIMIT": None,
}


SV_ATLAS_DB_LABEL = "default"  # NOTE: Ensures we pick up ATLAS pragma customizations on the default database
SV_ATLAS_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
if "SV_ATLAS_INGESTION_CONCURRENCY" in os.environ:
    SV_ATLAS_INGESTION_CONCURRENCY = int(os.environ["SV_ATLAS_INGESTION_CONCURRENCY"])

SV_ATLAS_INGESTION_PIPELINE = [
    "scaife_viewer.atlas.importers.versions.import_versions",
    "scaife_viewer.atlas.importers.text_annotations.import_text_annotations",
    "scaife_viewer.atlas.importers.attributions.import_attributions",
    "scaife_viewer.atlas.importers.metrical_annotations.import_metrical_annotations",
    "scaife_viewer.atlas.importers.image_annotations.import_image_annotations",
    "scaife_viewer.atlas.importers.audio_annotations.import_audio_annotations",
    "scaife_viewer.atlas.tokenizers.tokenize_all_text_parts",
    # TODO: Backport to scaife_viewer.atlas
    "scaife_stack_atlas.temp.load_token_annotations",
    "scaife_viewer.atlas.importers.named_entities.apply_named_entities",
    # TODO: Backport to scaife_viewer.atlas
    "scaife_stack_atlas.temp.process_alignments",
    "scaife_stack_atlas.temp.set_text_annotation_collection",
]
DB_DATA_PATH = os.environ.get("DB_DATA_PATH", PROJECT_ROOT)
SV_ATLAS_DB_PATH = os.path.join(DB_DATA_PATH, "db.sqlite")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SV_ATLAS_DB_PATH,
        # @@@ this timeout may not be appropriate
        # for all sites using scaife-viewer-atlas,
        # but we will likely have an ATLAS specific
        # database router / ingestion-specific
        # config in the future anyways
        "OPTIONS": {"timeout": 5 * 60},
    }
}
