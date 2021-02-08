from ..models import Playlist, Video


def store_video(video_blob, add_to_playlist=None):
    video = Video.query.filter(Video.video_id == video_blob["id"]).first()
    if video is None:
        video = Video()
        video.name = video_blob["title"]
        video.video_id = video_blob["id"]
        video.webpage_url = video_blob["webpage_url"]
        video.duration = video_blob["duration"]
        video.extractor = video_blob["extractor"]

    if add_to_playlist:
        video.playlists.append(add_to_playlist)

    return video


def store_playlist(playlist_blob):
    playlist = Playlist.query.filter(
        Playlist.playlist_id == playlist_blob["id"]
    ).first()
    if playlist is None:
        playlist = Playlist()
        playlist.name = playlist_blob["title"]
        playlist.playlist_id = playlist_blob["id"]
        playlist.extractor = playlist_blob["extractor"]
        playlist.webpage_url = playlist_blob["webpage_url"]

    return playlist
