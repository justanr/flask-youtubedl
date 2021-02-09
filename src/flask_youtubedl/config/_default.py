class DefaultConfiguration:
    SQLALCHEMY_DATABASE_URI = "sqlite:///fytdl.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False

    CELERY_CONFIG = {"broker_transport_options": {"max_retries": 1}}
