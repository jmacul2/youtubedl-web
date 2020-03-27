from datetime import datetime
from youtube_dl.YoutubeDL import YoutubeDL

from project import app, celery
from project.models import Download


@celery.task(bind=True, max_retries=None)
def ydl_download(self, download_id):
    with app.app_context():
        d = Download.query.filter_by(id=download_id).first()
        opts = {
            'outtmpl': d.outtmpl,
            'progress_hooks': [d.progress_hook],
            'format': d.ydl_format,
        }
        y = YoutubeDL(params=opts)
        y.download([d.url])