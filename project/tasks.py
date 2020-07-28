from datetime import datetime
from youtube_dl.YoutubeDL import YoutubeDL
from youtube_dl.utils import DownloadError

from project import app, celery
from project.models import Download, DownloadStatus


@celery.task(bind=True, max_retries=None)
def ydl_download(self, download_id):
    with app.app_context():
        d = Download.query.filter_by(id=download_id).first()
        opts = {
            'noplaylist': not d.playlist,
            'outtmpl': d.outtmpl,
            'progress_hooks': [d.progress_hook],
            'format': d.df.ydl_format,
            'sleep_interval': 60,
            'max_sleep_interval': 300,
        }
        y = YoutubeDL(params=opts)
        try:
            y.download([d.url])
        except DownloadError:
            d.status = DownloadStatus.ERROR
            d.save()
