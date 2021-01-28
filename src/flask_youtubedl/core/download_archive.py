import errno
import io
from abc import ABC, abstractmethod
from collections import defaultdict

from youtubedl.utils import locked_file as ytdl_locked_file

## eventually supply a sqlalchemy backed archive

class DownloadArchive(ABC):
    @abstractmethod
    def add(self, archive_name, vid):
        NotImplemented

    @abstractmethod
    def exists(self, archive_name, vid):
        NotImplemented

    @abstractmethod
    def remove(self, archive_name, vid):
        NotImplemented


class SetDownloadArchive(DownloadArchive):
    def __init__(self, archives=None):
        self._archives = defaultdict(set)

    def add(self, archive_name, vid):
        self._archives[archive_name].add(vid)

    def exists(self, archive_name, vid):
        return vid in self._archives[archive_name]

    def remove(self, archive_name, vid):
        self._archives[archive_name].remove(vid)


class _locked_file(ytdl_locked_file):
    def __init__(self, filename, mode, encoding=None):
        self.f = io.open(filename, mode, encoding=encoding)
        self.mode = mode

    def seek(self, destination):
        self.f.seek(destination)

    def truncate(self):
        self.f.truncate()


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

    def remove(self, archive_name, vid):
        with self._get_locked_file(archive_name, "r+") as fh:
            lines = list(fh)
            fh.seek(0)
            for line in lines:
                if line.strip() != vid:
                    fh.write(line)
            fh.truncate()

    def _get_locked_file(self, filename, mode, encoding="utf-8"):
        return locked_file(filename, mode, encoding)


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
