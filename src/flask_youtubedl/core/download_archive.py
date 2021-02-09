import errno
import io
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, MutableSet

from injector import ClassAssistedBuilder, inject
from redis import Redis
from youtube_dl.utils import locked_file

## eventually supply a sqlalchemy backed archive

__all__ = (
    "DownloadArchive",
    "SetDownloadArchive",
    "LockedFileDownloadArchive",
    "UseArchiveMixin",
)


class DownloadArchive(ABC):
    @abstractmethod
    def add(self, archive_name, vid):
        NotImplemented

    @abstractmethod
    def exists(self, archive_name, vid):
        NotImplemented


class SetDownloadArchive(DownloadArchive):
    def __init__(self, archives: Dict[str, Dict[str, MutableSet[str]]] = None):
        self._archives = (
            archives
            if archives is not None
            else defaultdict(SetDownloadArchive._archive_factory)
        )

    def add(self, archive_name, vid):
        (extractor, id) = vid.split(" ", 1)
        self._archives[archive_name][extractor].add(id)

    def exists(self, archive_name, vid):
        (extractor, id) = vid.split(" ", 1)
        return id in self._archives[archive_name][extractor]

    @staticmethod
    def _archive_factory():
        return defaultdict(set)


class LockedFileDownloadArchive(DownloadArchive):
    def exists(self, archive_name, vid):
        try:
            with self._get_locked_file(archive_name, "r") as fh:
                for line in fh:
                    if line.strip() == vid:
                        return True
        except IOError as ioe:
            if ioe.errno != errno.ENOENT:
                raise
        return False

    def add(self, archive_name, vid):
        with self._get_locked_file(archive_name, "a") as fh:
            fh.write(vid + "\n")

    def _get_locked_file(self, filename, mode, encoding="utf-8"):
        return locked_file(filename, mode, encoding)


class RedisDownloadArchive(DownloadArchive):
    def __init__(self, redis_conn: Redis):
        self._conn = redis_conn

    def add(self, archive_name, vid):
        self._conn.sadd(archive_name, vid)

    def exists(self, archive_name, vid):
        return self._conn.sismember(archive_name, vid)


class UseArchiveMixin:
    def __init__(self, *args, archive=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._dl_archive = archive or LockedFileDownloadArchive()

    def in_download_archive(self, info_dict):
        archive = self.params.get("download_archive")
        if not archive:
            return False

        vid = self._make_archive_id(info_dict)
        return vid and self._dl_archive.exists(archive, vid)

    def record_download_archive(self, info_dict):
        archive = self.params.get("download_archive")
        if not archive:
            return

        vid = self._make_archive_id(info_dict)
        if vid:
            self._dl_archive.add(archive, vid)


class DownloadArchiveFactory(ABC):
    @abstractmethod
    def get(self) -> DownloadArchive:
        raise NotImplementedError()


class GenericeDownloadArchiveFactory(DownloadArchiveFactory):
    def __init__(self, creator):
        self._creator = creator

    def get(self) -> DownloadArchive:
        return self._creator


class RedisDownloadArchiveFactory(DownloadArchiveFactory):
    @inject
    def __init__(self, redis_factory: ClassAssistedBuilder[Redis]) -> None:
        self._redis_factory = redis_factory

    def get(self) -> DownloadArchiveFactory:
        return RedisDownloadArchive(self._redis_factory.build())
