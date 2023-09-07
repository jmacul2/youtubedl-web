from flask import Blueprint, Response, render_template
from project import conf


blueprint = Blueprint('index', __name__)


@blueprint.route('/', methods=['GET'])
def index():
    return Response(
        render_template(
            'index.html',
        ),
        mimetype='text/html'
    )