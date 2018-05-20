import json
import random
import time

from celery import Celery
from celery.result import AsyncResult
from celery.worker.control import revoke
from flask import Flask
from flask import request
from flask.templating import render_template
from flask_redis import FlaskRedis
from youtube_dl.YoutubeDL import YoutubeDL

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',
    REDIS_URL='redis://localhost:6379/1'
)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
redis_store = FlaskRedis(app)


class Download:
    def __init__(self, json_content):
        try:
            j = json.loads(json_content)
        except TypeError:
            j = {}
        self.id = j.get('id', '')
        self.url = j.get('url', '')
        self.title = j.get('title', '')
        self.downloaded_bytes = j.get('downloaded_bytes', '')
        self.total_bytes = j.get('total_bytes', '')
        self.status = j.get('status', '')
        self.speed = j.get('speed', '')
        self.eta = j.get('eta', '')
        self.task_id = j.get('task_id', '')

    def to_json(self):
        return json.dumps(self.__dict__)

    def save(self):
        if self.id == '':
            self.id = int(time.time() * 1000) + random.randint(0,999)
        redis_store.set(self.id, self.to_json())
        return self

    @staticmethod
    def find(id):
        return Download(redis_store.get(id))

    @staticmethod
    def find_by_url(url):
        for result in redis_store.scan_iter('*'):
            try:
                item = json.loads(redis_store.get(result))
            except TypeError:
                # Result not found
                return None

            if item.get('url') == url:
                return item

    def delete(self):
        redis_store.delete(self.id)

    def set_details(self, info):
        try:
            self.title = info.get(
                'tmpfilename'
            ).replace('.part', '').replace('/downloads/', '')
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
        self.save()


@celery.task
def download(id):
    with app.app_context():
        d = Download.find(id)
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
    return json.dumps(
        [json.loads(redis_store.get(x).decode()) for x in redis_store.scan_iter('*')]
    )


@app.route('/add', methods=['POST'])
def add_download():
    data = json.loads(request.data.decode())
    for url in data['url'].split('\n'):
        # Check if it exists
        q = Download.find_by_url(url)
        if q is None and url != '':
            # Store URL
            d = Download(json.dumps({'url': url, 'title': url}))
            d = d.save()

            # Create task to download
            task = download.delay(d.id)
            d.task_id = task.id
            d.status = 'pending'
            d.save()

    return 'OK', 201


@app.route('/remove/<int:id>', methods=['DELETE'])
def remove_download(id):
    d = Download.find(id)
    task = AsyncResult(d.task_id)
    try:
        if not task.ready():
            revoke(d.task_id, terminate=True)
    except Exception:
        pass

    d.delete()
    return 'OK', 200


@app.route('/restart/<int:id>', methods=['POST'])
def restart_download(id):
    download.delay(id)
    return 'OK', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0')
