import os
import logging

class BaseConfig:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_LOCATION = 'downloader.log'
    LOGGING_LEVEL = logging.DEBUG
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    BCRYPT_LOG_ROUNDS = 13
    TOKEN_EXPIRATION_DAYS = 30
    TOKEN_EXPIRATION_SECONDS = 0
    TOKEN_PASSWORD_EXPIRATION_DAYS = 1
    TOKEN_PASSWORD_EXPIRATION_SECONDS = 0
    TOKEN_EMAIL_EXPIRATION_DAYS = 1
    TOKEN_EMAIL_EXPIRATION_SECONDS = 0
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
    CELERY_DEFAULT_QUEUE = os.environ.get('CELERY_DEFAULT_QUEUE', 'celery')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    #SENTRY_DSK = os.environ.get('SENTRY_DSN')

    DEFAULT_YDL_FORMAT = os.environ.get('DEFAULT_YDL_FORMAT', 'best')
    DEFAULT_YDL_TEMPLATE = os.environ.get('DEFAULT_YDL_TEMPLATE', '%(title)s.%(ext)s')
    BASE_DOWNLOAD_PATH = os.environ.get('BASE_DOWNLOAD_PATH')

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    #BCRYPT_LOG_ROUNDS = 4

class TestingConfig(BaseConfig):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_TEST_URL')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_TEST_URL')
    CELERY_TASK_ALWAYS_EAGER = True
    #BCRYPT_LOG_ROUNDS = 4
    TOKEN_EXPIRATION_DAYS = 0
    TOKEN_EXPIRATION_SECONDS = 3
    TOKEN_PASSWORD_EXPIRATION_DAYS = 0
    TOKEN_PASSWORD_EXPIRATION_SECONDS = 2
    TOKEN_EMAIL_EXPIRATION_DAYS = 1
    TOKEN_EMAIL_EXPIRATION_SECONDS = 0
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    SENTRY_DSN = 'Sentry_DSN'
