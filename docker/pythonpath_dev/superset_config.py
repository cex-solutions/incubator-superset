# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#

import logging
import os
from typing import Optional

from werkzeug.contrib.cache import FileSystemCache

logger = logging.getLogger()


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "The environment variable {} was missing, abort...".format(
                var_name
            )
            raise EnvironmentError(error_msg)


DATABASE_DIALECT = get_env_variable("DB_DIALECT")
DATABASE_USER = get_env_variable("DB_USER")
DATABASE_PASSWORD = get_env_variable("DB_PASSWORD")
DATABASE_HOST = get_env_variable("DB_HOST")
DATABASE_PORT = get_env_variable("DB_PORT")
DATABASE_DB = get_env_variable("SUPERSET_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = "%s://%s:%s@%s:%s/%s" % (
    DATABASE_DIALECT,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB,
)

REDIS_HOST = get_env_variable("REDIS_HOST")
REDIS_PORT = get_env_variable("REDIS_PORT")

RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")


class CeleryConfig(object):
    BROKER_URL = "redis://%s:%s/0" % (REDIS_HOST, REDIS_PORT)
    CELERY_IMPORTS = ("superset.sql_lab",)
    CELERY_RESULT_BACKEND = "redis://%s:%s/1" % (REDIS_HOST, REDIS_PORT)
    CELERY_ANNOTATIONS = {"tasks.add": {"rate_limit": "10/s"}}
    CELERY_TASK_PROTOCOL = 1


CELERY_CONFIG = CeleryConfig

SECRET_KEY = "tQIhoYJb8um9MNFisieL9jS3+gcEw95Lfc/EQHKR58prOMJQKx"
#
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden
#
try:
    from superset_config_docker import *  # noqa
    import superset_config_docker

    logger.info(
        f"Loaded your Docker configuration at " f"[{superset_config_docker.__file__}]"
    )
except ImportError:
    logger.info("Using default Docker config...")

HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}


from jose import jwt
from flask_login import login_user

from flask import request


class CexData:
    database: str
    user_id: int

    def __init__(self, database: str, user_id: int):
        self.database = database
        self.user_id = user_id


class TokenAuth:
    def __init__(self, app):
        self.app = app

    def before_request(self):
        from superset import security_manager as sm

        environ = request.environ
        if "HTTP_COOKIE" in environ and "auth_token" in environ.get("HTTP_COOKIE"):
            http_cookies: str = environ.pop("HTTP_COOKIE", None)
            logger.debug("found cookies")
            auth_cookie = [
                cookie
                for cookie in http_cookies.split("; ")
                if cookie.startswith("auth_token")
            ]
            if auth_cookie:
                auth_cookie = auth_cookie[0]
                logger.debug(f"found auth cookie {auth_cookie}")
                decoded_token = jwt.get_unverified_claims(
                    auth_cookie.split("auth_token=")[1]
                )
                logger.debug(f"decoded_token {decoded_token}")
                role = decoded_token.get("cex", {}).get("role")
                logger.debug(f"setting user: ")
                logger.debug(role)
                environ["REMOTE_USER"] = role
                environ["user_id"] = decoded_token.get("cex", {}).get("uid")
                environ["role"] = decoded_token.get("cex", {}).get("role")
                environ["database"] = "cex_blp"
                user = sm.find_user(username=role)
                if user:
                    logger.debug("login user")
                    login_user(user)
        else:
            environ["user_id"] = 1
            environ["role"] = "sfe"
            environ["database"] = "cex"


from superset.app import SupersetAppInitializer


def app_init(app):
    logging.info("Registering RemoteUserLogin")
    app.before_request(TokenAuth(app).before_request)
    return SupersetAppInitializer(app)


APP_INIT = app_init


def current_user_id():
    return request.environ.get("user_id")


def database():
    return request.environ.get("database")


def role():
    return request.environ.get("role")


context_addons = {
    "cex_user_id": lambda: current_user_id(),
    "cex_database": lambda: database(),
    "cex_role": lambda: role(),
}

JINJA_CONTEXT_ADDONS = context_addons
