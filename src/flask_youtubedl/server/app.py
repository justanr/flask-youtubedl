from flask import Flask, jsonify
from youtube_dl import YoutubeDL

ytdl = YoutubeDL()
ytdl.add_default_info_extractors()

app = Flask(__name__)

@app.route("/info/playlist/<id>")
def playlist_info(id):
    info = ytdl.extract_info(f"https://www.youtube.com/playlist?list={id}", download=False)
    return jsonify(info)

@app.route("/info/video/<id>")
def video_info(id):
    info = ytdl.extract_info(f"https://www.youtube.com/watch?v={id}", download=False)
    return jsonify(info)

if __name__ == "__main__":
    app.run(use_reloader=True, debug=True)
