from uuid import uuid4

from flask.views import MethodView
from injector import inject
from sqlalchemy.orm import Session
from youtube_dl import YoutubeDL

from ..core.schema import DownloadSchema
from ..core.utils import store_video
from ..models import Download, Video
from ._helpers import FytdlBlueprint
from .serialize import serialize_with
from ..worker.tasks import process_video_download

download = FytdlBlueprint("download", __name__, url_prefix="/download")


class DownloadView(MethodView):
    @inject
    def __init__(self, ytdl: YoutubeDL, session: Session):
        self._ytdl = ytdl
        self._session = session

    @serialize_with(schema=DownloadSchema)
    def post(self, id: str):
        dl = (
            Download.query.join(Video, Download.video)
            .filter(Video.video_id == id)
            .first()
        )

        if dl is None or dl.status.lower() == "failed":
            info = self._ytdl.extract_info(
                f"https://www.youtube.com/watch?v={id}", download=False
            )
            video = store_video(info)
            dl = Download()
            dl.download_id = str(uuid4())
            dl.video = video
            self._session.add(dl)
            self._session.commit()
            process_video_download.delay(str(dl.download_id))

        return dl


download.add_url_rule("/video/<id>", view_func=DownloadView.as_view("download"))
