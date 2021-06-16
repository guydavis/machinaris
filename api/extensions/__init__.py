"""Extensions initialization"""

from common.extensions import database
from .api import Api


def create_api(app):

    api = Api(app)

    for extension in (
            database,
    ):
        extension.init_app(app)

    return api