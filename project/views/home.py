from flask import Blueprint, Response, render_template
from project import conf


blueprint = Blueprint('home', __name__)


@blueprint.route('/', methods=['GET'])
def home():
    return Response(
        render_template(
            'index.html',
        ),
        mimetype='text/html'
    )