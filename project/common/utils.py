from contextlib import contextmanager

from project import conf
from project.common.exceptions import APIException, ServerErrorException


@contextmanager
def session_scope(session):
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        raise ServerErrorException()
