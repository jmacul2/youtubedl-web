import os
import json
import random
import time

from datetime import datetime, timedelta
from celery import Celery
from celery.result import AsyncResult
from celery.worker.control import revoke
from flask import Flask
from flask import request, flash
from flask.templating import render_template
from flask_redis import FlaskRedis
from youtube_dl.YoutubeDL import YoutubeDL
from config import config, logger

app = Flask(__name__)
app.config.update(
    SECRET_KEY=config.SECRET_KEY,
    CELERY_BROKER_URL=config.CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND=config.CELERY_RESULT_BACKEND,
    REDIS_URL=config.REDIS_URL,
)
celery = Celery(
    app.name, backend='rpc://', broker=app.config['CELERY_BROKER_URL']
)
redis_store = FlaskRedis(app)


class Download:
    def __init__(self, json_content):
        try:
            # hack of the day
            if isinstance(json_content, bytes):
                json_content = json_content.decode()
            j = json.loads(json_content)
        except TypeError:
            logger.warning('json_content provided to Download class failed to load')
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
        self.last_update = j.get('last_update', '')
        self.format = j.get('format', '')

        if self.last_update != '':
            timestamp = datetime.strptime(self.last_update, '%Y-%m-%d %H:%M:%S')
            two_mins_ago = timestamp + timedelta(minutes=2)
            if two_mins_ago < datetime.now() and self.status != 'finished':
                self.stuck = True
            else:
                self.stuck = False
        else:
            self.stuck = False

    def to_json(self):
        return json.dumps(self.__dict__)

    def save(self):
        if self.id == '':
            self.id = 'ydl_{}'.format(int(time.time() * 1000) + random.randint(0, 999))
        redis_store.set(self.id, self.to_json())
        return self

    @staticmethod
    def find(id):
        return Download(redis_store.get(id))

    @staticmethod
    def find_by_url(url):
        logger.debug('find by url: {}'.format(url))
        for result in redis_store.scan_iter('ydl_*'):
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
            ).replace('.part', '').replace(self.format['path'], '')
        except Exception as ex:
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
        self.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save()


def within_allowed_hours():
    # Check that current time is within allowed hours
    if not (config.DOWNLOAD_START and config.DOWNLOAD_STOP):
        return True
    now = datetime.now()
    start_hour = config.DOWNLOAD_START
    stop_hour = config.DOWNLOAD_STOP
    if start_hour > stop_hour:
        allow_downloads = start_hour < now.hour or now.hour < stop_hour
    else:
        allow_downloads = start_hour < now.hour < stop_hour
    if allow_downloads:
        return True
    return False
        

@celery.task(bind=True, max_retries=None)
def download(self, id):
    
    if not within_allowed_hours():
        now = datetime.now()
        eta = datetime(now.year, now.month, now.day, config.DOWNLOAD_START, 0, 0)
        if eta < now:
            eta = eta + timedelta(days=1)
        eta = eta + timedelta(seconds=random.randint(300))
        raise self.retry(eta=eta)

    with app.app_context():
        d = Download.find(id)
        opts = {
            'outtmpl': d.format['path'] + d.format['template'],
            'progress_hooks': [d.set_details],
            'format': d.format['ydl_format'],
        }
        y = YoutubeDL(params=opts)
        try:
            y.download([d.url])
        except:
            # TODO catch YDL error for missing format or other -> mark item failed
            pass


@app.route('/')
def index():
    return render_template('index.html', title=config.TITLE)


@app.route('/formats')
def get_formats():
    return json.dumps([f['name'] for f in config.FORMATS])


@app.route('/downloads')
def get_downloads():
    result = []
    enough = 0
    for i in redis_store.scan_iter('ydl_*'):
        d = Download(redis_store.get(i).decode())
        if d.status != 'finished':
            result.append(json.loads(d.to_json()))
        else:
            if enough < 5:
                result.append(json.loads(d.to_json()))
                enough += 1
    return json.dumps(
        sorted(result, key=lambda x: (x['last_update']))
    )


@app.route('/downloads/status/<string:status>')
def get_downloads_status(status):
    result = []
    for i in redis_store.scan_iter('ydl_*'):
        try:
            item = json.loads(redis_store.get(i))
        except TypeError:
            # Result not found
            return None
        if item.get('status') == status:
            result.append(item)
    return json.dumps(
        sorted(result, key=lambda x: (x['last_update']))
    )


@app.route('/downloads/format/<string:fmt>')
def get_downloads_format(fmt):
    result = []
    for i in redis_store.scan_iter('ydl_*'):
        try:
            item = json.loads(redis_store.get(i))
        except TypeError:
            # Result not found
            return None
        if item.get('format') == fmt:
            result.append(item)
    return json.dumps(
        sorted(result, key=lambda x: (x['last_update']))
    )


@app.route('/add', methods=['POST'])
def add_download():
    data = json.loads(request.data.decode())
    count = 0
    cc = 0
    fmt = config.FORMATS[int(data['format'])]
    for url in data['url'].split('\n'):
        # Check if it exists
        q = Download.find_by_url(url)
        if (q is None or q.get('format', '') != fmt) and url != '':
            # Store URL
            d = Download(json.dumps({'url': url, 'title': url, 'format': fmt}))
            d = d.save()

            # Create task to download
            task = download.delay(d.id)
            d.task_id = task.id
            d.status = 'pending'
            d.save()

            count += 1
        else:
            cc += 1

    return 'OK', 201


@app.route('/remove/<id>', methods=['DELETE'])
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


@app.route('/restart/<id>', methods=['POST'])
def restart_download(id):
    new = download.apply_async([id], countdown=5)
    existing = Download.find(id)
    existing.task_id = new.task_id
    existing.save()
    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0')
