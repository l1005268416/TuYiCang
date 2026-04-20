import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from flask_cors import CORS

from app.app_context import create_app

# Setup logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info("Starting TuYiCang on %s:%d", host, port)
    logger.info("Environment: debug=%s", debug)

    app = create_app()
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    })

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
