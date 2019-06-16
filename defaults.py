DEBUG = 1

SECRET_KEY = 'super-secret-key'

DEFAULT_DOWNLOAD_PATH = '/downloads/'

DEFAULT_OUTPUT_TEMPLATE = '%(title)s-%(id)s.%(ext)s'

FORMATS = [
    {
        'name': 'Best',
        'ydl_format': 'bestvideo+bestaudio',
    }
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'

CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

REDIS_URL = 'redis://localhost:6379/1'