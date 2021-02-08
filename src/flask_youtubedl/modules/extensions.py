from sqlalchemy.orm import Session

from injector import provider

from ..extensions import db
from ._helpers import FytdlModule


class ExtensionsModule(FytdlModule):
    @provider
    def provide_session(self) -> Session:
        return db.session
