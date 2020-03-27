import datetime, os, logging
from flask import Flask
from flask_cors import CORS


class BaseFlask(Flask):

    def __init__(
        self,
        import_name
    ):
        Flask.__init__(
            self,
            import_name,
            static_folder='./static',
            template_folder='./templates'
        )
        # set config
        app_settings = os.getenv('APP_SETTINGS')
        self.config.from_object(app_settings)

        # configure logging
        handler = logging.FileHandler(self.config['LOGGING_LOCATION'])
        handler.setLevel(self.config['LOGGING_LEVEL'])
        handler.setFormatter(logging.Formatter(self.config['LOGGING_FORMAT']))
        self.logger.addHandler(handler)

        # enable CORS
        CORS(self)