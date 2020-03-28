import os

from flask import Blueprint, request
from celery.result import AsyncResult
from celery.worker.control import revoke
from werkzeug.utils import secure_filename

from project import conf, db
from project.models import Download, DownloadFormat
from project.common.utils import session_scope
from project.common.exceptions import InvalidPayload, NotFoundException, BusinessException


blueprint = Blueprint('api', __name__, template_folder=None)


def get_download_paths():
    paths = []
    base_dir = conf.get('BASE_DOWNLOAD_PATH')
    base_length = len(base_dir)
    for root, subdirs, files in os.walk(base_dir):
        paths.append(root[base_length:])
    return paths


@blueprint.route('/downloads', methods=['GET'])
def downloads():
    downloads = Download.query.all()
    data = [d.to_dict() for d in downloads] if downloads else []
    return {
        'status': 'success',
        'data': data
    }


@blueprint.route('/add', methods=['POST'])
def add_download():
    data = request.get_json()
    if not data:
        raise InvalidPayload(message='Payload missing')

    urls = data.get('url', '').split('\n')
    name = data.get('format')

    # Prepare the download path
    path = data.get('path')
    if path not in get_download_paths():
        raise InvalidPayload(message='path is not valid')
    extendedPath = secure_filename(data.get('extendedPath', ''))
    if extendedPath:
        path = os.path.join(path, extendedPath)
    path = conf.get('BASE_DOWNLOAD_PATH') + path  # TODO must be better way
    if not os.path.exists(path):
        import pdb; pdb.set_trace()
        os.makedirs(path)

    df = DownloadFormat.query.filter_by(name=name).first()
    if df and urls and path:
        for url in urls:
            existing = Download.query.filter_by(url=url).first()
            if existing is None and url != '':
                # Save the download
                with session_scope(db.session) as session:
                    dl = Download(url, path, df)
                    session.add(dl)
                # Create the download task
                from project.tasks import ydl_download
                task = ydl_download.delay(dl.id)
                dl.task_id = task.id
                dl.save()
        return {
            'status': 'success',
            'message': 'Added'
        }
    raise InvalidPayload()


@blueprint.route('/update/<int:id>', methods=['POST'])
def update_download(id):
    pass


@blueprint.route('/restart/<int:id>', methods=['POST'])
def restart_download(id):
    from project.tasks import ydl_download
    new = ydl_download.apply_async([id], countdown=10)
    existing = Download.query.filter_by(id=id).first()
    existing.task_id = new.task_id
    existing.save()
    return {
        'status': 'success',
        'message': f'Restarted download {id}'
    }


@blueprint.route('/remove/<int:id>', methods=['DELETE'])
def remove_download(id):
    d = Download.query.filter_by(id=id).first()
    if d:
        task_id = d.task_id
        task = AsyncResult(task_id)
        try:
            if not task.ready():
                revoke(task_id, terminate=True)
        except Exception:
            pass

        d.delete()
        return {
            'status': 'success',
            'message': f'Task {task_id} revoked and download {id} removed'
        }
    raise NotFoundException()


@blueprint.route('/formats', methods=['GET'])
def formats():
    dfs = DownloadFormat.query.all()
    data = [df.to_dict() for df in dfs]
    return {
        'status': 'success',
        'data': data
    }


@blueprint.route('/paths', methods=['GET'])
def paths():
    paths = get_download_paths()
    return {
        'status': 'success',
        'data': paths
    }