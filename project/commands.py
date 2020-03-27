from datetime import datetime

import click
from flask.cli import AppGroup

from project import conf, db
from project.models import DownloadFormat
from project.common.utils import session_scope


cli = AppGroup('format', help='Commands for download formats.')


@cli.command('add')
@click.option('--name', prompt=True)
@click.option('--ydl-format', prompt=True, default=conf.get('DEFAULT_YDL_FORMAT'), show_default=conf.get('DEFAULT_YDL_FORMAT'))
@click.option('--ydl-template', prompt=True, default=conf.get('DEFAULT_YDL_TEMPLATE'), show_default=conf.get('DEFAULT_YDL_TEMPLATE'))
def add(name, ydl_format, ydl_template):
    print(name, ydl_format, ydl_template)
    df = DownloadFormat(name=name, ydl_format=ydl_format, ydl_template=ydl_template)
    with session_scope(db.session) as session:
        session.add(df)
