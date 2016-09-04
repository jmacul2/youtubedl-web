from celery.result import AsyncResult
from celery.worker.control import revoke
from flask import Flask
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy

from celery import Celery
from flask import request
import json

from youtube_dl.YoutubeDL import YoutubeDL

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',
    SQLALCHEMY_DATABASE_URI='sqlite:////tmp/test.db'
)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
db = SQLAlchemy(app)


class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    url = db.Column(db.String(255))
    downloaded_bytes = db.Column(db.BigInteger)
    total_bytes = db.Column(db.BigInteger)
    status = db.Column(db.String(255))
    speed = db.Column(db.String(255))
    eta = db.Column(db.String(255))
    task_id = db.Column(db.BigInteger)

    def __init__(self, url=None, title=None):
        self.url = url
        self.title = title

    def to_json(self):
        return {c.name: getattr(self, c.name) or '' for c in self.__table__.columns}

    def set_details(self, info):
        try:
            self.title = info.get('tmpfilename').replace('.part', '').replace('/downloads/', '')
        except Exception:
            pass

        # Already completed downloads don't have `downloaded_bytes`
        if info.get('status') != 'finished':
            self.downloaded_bytes = info.get('downloaded_bytes', 0)
        else:
            self.downloaded_bytes = info.get('total_bytes')

        self.total_bytes = info.get('total_bytes', 0)
        self.speed = info.get('_speed_str', '')
        self.status = info.get('status', 'pending')
        self.eta = info.get('_eta_str', '')

        db.session.commit()


db.create_all()


@celery.task
def download(id):
    with app.app_context():
        d = Download.query.get(id)
        opts = {
            'outtmpl': '/downloads/%(title)s-%(id)s.%(ext)s',
            'progress_hooks': [d.set_details]
        }
        y = YoutubeDL(params=opts)
        y.download([d.url])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/downloads')
def get_downloads():
    return json.dumps([x.to_json() for x in Download.query.all()])


@app.route('/add', methods=['POST'])
def add_download():
    data = json.loads(request.data.decode())
    for url in data['url'].split('\n'):
        # Check if it exists
        q = Download.query.filter_by(url=url).first()
        if q is None and url != '':
            # Store URL
            d = Download(url=url, title=url)
            db.session.add(d)
            db.session.commit()

            # Create task to download
            task = download.delay(d.id)
            d.task_id = task.id
            d.status = 'pending'
            db.session.commit()

    return 'OK', 201


@app.route('/remove/<int:id>', methods=['DELETE'])
def remove_download(id):
    d = Download.query.get(id)
    task = AsyncResult(d.task_id)
    try:
        if not task.ready():
            revoke(d.task_id, terminate=True)
    except Exception:
        pass
    db.session.delete(d)
    db.session.commit()
    return 'OK', 200


@app.route('/restart/<int:id>', methods=['POST'])
def restart_download(id):
    download.delay(id)
    return 'OK', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0')
