from flask import Flask, jsonify, request
from flask_cors import CORS
from ytmusicapi import YTMusic

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.json.ensure_ascii = False
CORS(app)

_yt = None


def get_ytmusic():
    global _yt
    if _yt is None:
        _yt = YTMusic()
    return _yt


@app.route("/search")
def search():
    query = request.args.get("q")

    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        yt = get_ytmusic()
        results = yt.search(query, filter="songs")

        if not results:
            return jsonify({"error": "No song found"}), 404

        songs = []

        for song in results[:10]:
            artists = song.get("artists") or []
            thumbnails = song.get("thumbnails") or []
            video_id = song.get("videoId")

            lyrics_lines = None

            if video_id:
                watch = yt.get_watch_playlist(video_id)
                browse_id = watch.get("lyrics")

                if browse_id:
                    lyrics_data = yt.get_lyrics(browse_id)
                    lyrics_text = lyrics_data.get("lyrics")
                    if isinstance(lyrics_text, str):
                        lyrics_lines = lyrics_text.splitlines()

            songs.append({
                "artist": artists[0].get("name") if artists else None,
                "lyricsLines": lyrics_lines,
                "thumbnail": thumbnails[-1].get("url") if thumbnails else None,
                "title": song.get("title"),
                "videoId": video_id,
            })

        return jsonify(songs)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/song")
def song():
    videoId = request.args.get("videoId")

    if not videoId:
        return jsonify({"error": "Missing videoId"}), 400

    yt = get_ytmusic()
    watch = yt.get_watch_playlist(videoId)

    return jsonify({
        "videoId": videoId,
        "title": watch.get("tracks", [{}])[0].get("title"),
        "artist": watch.get("tracks", [{}])[0].get("artists", [{}])[0].get("name"),
        "lyricsId": watch.get("lyrics")
    })


@app.route("/lyrics")
def lyrics():
    videoId = request.args.get("videoId")

    if not videoId:
        return jsonify({"error": "Missing videoId"}), 400

    try:
        yt = get_ytmusic()
        watch = yt.get_watch_playlist(videoId)
        browseId = watch.get("lyrics")

        if not browseId:
            return jsonify({"lyricsLines": None})

        lyrics_data = yt.get_lyrics(browseId)
        lyrics_text = lyrics_data.get("lyrics")

        lyrics_lines = None
        if isinstance(lyrics_text, str):
            lyrics_lines = lyrics_text.splitlines()

        return jsonify({
            "lyricsLines": lyrics_lines,
            "source": lyrics_data.get("source")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return jsonify({"status": "API running - Api by Varad"})


if __name__ == "__main__":
    app.run(debug=True)
