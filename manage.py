import click
import pytest
import urllib.parse

import sys
import subprocess

from flask.cli import FlaskGroup
#from flask_migrate import MigrateCommand

from project import create_app, conf, db


cli = FlaskGroup(create_app=create_app)


@cli.command()
@click.argument('queue', default=conf.get('CELERY_DEFAULT_QUEUE'))
@click.option('--concurrency', '-c', default=1, type=int)
def celery_worker(queue, concurrency):
    """Starts the celery worker."""
    ret = subprocess.call(
        ['celery', 'worker', '-A', 'project.celery', '-l', 'INFO', '-c', str(concurrency), '-Q', queue])
    sys.exit(ret)


@cli.command()
def celery_beat():
    """Starts the celery task schedule."""
    ret = subprocess.call(
        ['celery', 'beat', '-A', 'project.celery', '-l', 'INFO'])
    sys.exit(ret)


@cli.command()
@click.argument('path', default='tests')
@click.option('--pdb', is_flag=True, default=False)
def test(path, pdb):
    """Runs the tests without code coverage."""
    if pdb:
        pytest.main([path, '-v', '-l', '--pdb'])    
    else:
        pytest.main([path, '-v', '-l'])


@cli.command()
def recreate_db():
    """Recreates a database."""
    #raise click.Abort()
    db.reflect()
    db.drop_all()
    db.create_all()
    db.session.commit()


'''
@cli.command()
def seed_db():
    """Seeds the database."""
    event_desc = EventDescriptor(id=1, name="Seed Events Name", description="Seed db Event from {1}")
    db.session.add(event_desc)
    group = Group(name="Group Name")
    db.session.add(group)
    user1 = User(username='martin', email="a@a.com", password="password", cellphone_number="98983510", cellphone_cc="+598")
    user2 = User(username='barreto', email="b@b.com", password="password")
    user3 = User(username='cheluskis', email="c@c.com", password="password")
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(user3)
    user_group_association1 = UserGroupAssociation(user=user1, group=group)
    db.session.add(user_group_association1)
    user_group_association2 = UserGroupAssociation(user=user2, group=group)
    db.session.add(user_group_association2)
    user_group_association3 = UserGroupAssociation(user=user3, group=group)
    db.session.add(user_group_association3)
    db.session.commit()
'''

if __name__ == '__main__':
    cli()
