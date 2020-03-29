import os
import json
from enum import IntEnum
from datetime import datetime, timedelta

from sqlalchemy.ext.hybrid import hybrid_property

from project import conf, db
from project.common.utils import session_scope


class DownloadFormat(db.Model):
    __tablename__ = 'downloads_formats'

    id = db.Column('id', db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True, index=True)
    ydl_format = db.Column(db.String, nullable=False)
    ydl_template = db.Column(db.String, nullable=False)

    def __init__(self, name: str, ydl_format: str=None, ydl_template: str=None):
        self.name = name
        if not ydl_format:
            ydl_format = conf.get('DEFAULT_YDL_FORMAT')
        self.ydl_format = ydl_format
        if not ydl_template:
            ydl_template = conf.get('DEFAULT_YDL_TEMPLATE')
        self.ydl_template = ydl_template

    def __repr__(self):
        return f'<DownloadFormat({self.name})>'

    def to_dict(self):
        return dict(
            name=self.name,
            format=self.ydl_format,
            template=self.ydl_template,
        )


class DownloadStatus:
    # YoutubeDL defined statuses
    PENDING = 'pending'
    DOWNLOADING = 'downloading'
    FINISHED = 'finished'
    ERROR = 'error'


class Download(db.Model):
    __tablename__ = 'downloads'

    id = db.Column('id', db.Integer, nullable=False, primary_key=True)
    url = db.Column(db.String, nullable=False, unique=True, index=True)
    title = db.Column(db.String)
    downloaded_bytes = db.Column(db.Integer)
    total_bytes = db.Column(db.Integer)
    status = db.Column(db.String, nullable=False, default=DownloadStatus.PENDING)
    speed = db.Column(db.String)
    eta = db.Column(db.String)
    _task_id = db.Column('task_id', db.String)
    _path = db.Column('path', db.String)
    playlist = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime)
    # Relationships
    df_id = db.Column(db.Integer, db.ForeignKey('downloads_formats.id'), nullable=False)
    df = db.relationship('DownloadFormat', backref=db.backref('downloads', cascade='all, delete-orphan'))

    def __init__(self, url: str, path: str, playlist: bool, df: DownloadFormat, created_at: datetime=datetime.utcnow()):
        self.url = url
        self.title = url
        self._path = path
        self.playlist = playlist
        self.df = df
        self.created_at = created_at

    def __repr__(self):
        return f'<Download({self.id} - {self.status})>'

    @property
    def stuck(self):
        if self.last_update:
            two_min_ago = self.last_update + timedelta(minutes=2)
            return two_min_ago < datetime.utcnow() and self.status != DownloadStatus.FINISHED
        return False

    @property
    def outtmpl(self):
        return os.path.join(self._path, self.df.ydl_template)

    @property
    def task_id(self):
        return self._task_id

    @task_id.setter
    def task_id(self, tid):
        self._task_id = tid
        self.status = DownloadStatus.PENDING

    def progress_hook(self, info):
        # Already completed downloads don't have `downloaded_bytes`
        try:
            self.title = info.get(
                'tmpfilename'
            ).replace('.part', '').replace(self._path, '')  #[1:]  # remove leading slash
        except Exception as ex:
            pass
        
        if info.get('status') != DownloadStatus.FINISHED:
            self.downloaded_bytes = info.get('downloaded_bytes', 0)
        else:
            self.downloaded_bytes = info.get('total_bytes')

        self.total_bytes = info.get('total_bytes', 0)
        self.speed = info.get('_speed_str', '')
        self.status = info.get('status', DownloadStatus.PENDING)
        self.eta = info.get('_eta_str', '')
        self.save()

    def save(self):
        with session_scope(db.session) as session:
            self.last_update = datetime.utcnow()  # XXX update last_seen... this may not be explicit enough
            session.add(self)

    def delete(self):
        with session_scope(db.session) as session:
            session.delete(self)

    def to_dict(self):
        return dict(
            id=self.id,
            url=self.url,
            title=self.title,
            path=self._path,
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_bytes,
            status=self.status,
            speed=self.speed,
            eta=self.eta,
            stuck=self.stuck,
            task_id=self.task_id,
            df=dict(
                name=self.df.name,
                format=self.df.ydl_format,
            ),
            last_update=self.last_update,
        )


class FailedTask(db.Model):
    __tablename__ = 'tasks_fails'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.String(36), nullable=False)
    full_name = db.Column(db.String, nullable=False)
    name = db.Column(db.String(125))
    args = db.Column(db.String)
    kwargs = db.Column(db.String)
    exception_class = db.Column(db.String, nullable=False)
    exception_msg = db.Column(db.String, nullable=False)
    traceback = db.Column(db.String)
    failures = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    def __init__(self, task_id: str, full_name: str, name: str, exception_class: str,
        exception_msg: str, traceback: str=None, created_at: datetime=datetime.utcnow()):
        self.task_id = task_id
        self.full_name = full_name
        self.name = name
        self.exception_class = exception_class
        self.exception_msg = exception_msg
        self.traceback = traceback
        self.created_at = created_at
        self.updated_at = created_at

    def retry_and_delete(self, inline=False):

        import importlib

        mod_name, func_name = self.full_name.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)

        args = json.loads(self.args) if self.args else {}
        kwargs = json.loads(self.kwargs) if self.kwargs else {}
        if inline:
            try:
                res = func(*args, **kwargs)
                self.delete()
                return res
            except Exception as exc:
                raise exc
        
        self.delete()
        return func.delay(*args, **kwargs)

    def delete(self):
        with session_scope(db.session) as session:
            session.delete(self)
    
    def save(self):
        with session_scope(db.session) as session:
            session.add(self)
