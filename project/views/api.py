import os

from flask import Blueprint, request
from werkzeug.utils import secure_filename

from project import conf, db
from project.models import DownloadStatus, Download, DownloadFormat
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
    if downloads:
        #data = [d.to_dict() for d in downloads]
        data = []
        return {
            'status': 'success',
            'data': data
        }
    raise NotFoundException


@blueprint.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    if not data:
        raise InvalidPayload(message='Payload missing')

    urls = data.get('url').split('\n')
    name = data.get('format')
    path = data.get('path')
    if path not in get_download_paths():
        raise InvalidPayload(message='path is not valid')
    extendedPath = secure_filename(data.get('extendedPath'))
    if extendedPath:
        path = os.path.join(path, extendedPath)

    df = DownloadFormat.query.filter_by(name=name).first()
    if df and path:
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
                with session_scope(db.session) as session:
                    dl.task_id = task.id
                    dl.status = DownloadStatus.PENDING
                    session.add(dl)
        return {
            'status': 'success',
            'message': 'Added'
        }
    raise InvalidPayload(message='Payload invalid')


@blueprint.route('/update', methods=['POST'])
def update():
    pass


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