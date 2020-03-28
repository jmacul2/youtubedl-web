from datetime import datetime
from youtube_dl.YoutubeDL import YoutubeDL
from youtube_dl.utils import DownloadError

from project import app, celery, db
from project.models import Download, DownloadStatus
from project.common.utils import session_scope


@celery.task(bind=True, max_retries=None)
def ydl_download(self, download_id):
    with app.app_context():
        d = Download.query.filter_by(id=download_id).first()
        opts = {
            'outtmpl': d.outtmpl,
            'progress_hooks': [d.progress_hook],
            'format': d.df.ydl_format,
        }
        y = YoutubeDL(params=opts)
        try:
            y.download([d.url])
        except DownloadError:
            with session_scope(db.session) as session:
                d.status = DownloadStatus.ERROR
                d.updated_at = datetime.utcnow()
                session.add(d)