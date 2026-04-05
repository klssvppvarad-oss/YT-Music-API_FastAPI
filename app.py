from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="YT Music API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_yt = None


def get_ytmusic():
    global _yt
    if _yt is None:
        from ytmusicapi import YTMusic

        _yt = YTMusic()
    return _yt


def build_song_result(song):
    artists = song.get("artists") or []
    thumbnails = song.get("thumbnails") or []
    video_id = song.get("videoId")
    lyrics_lines = None

    if video_id:
        try:
            yt = get_ytmusic()
            watch = yt.get_watch_playlist(video_id)
            browse_id = watch.get("lyrics")

            if browse_id:
                lyrics_data = yt.get_lyrics(browse_id)
                lyrics_text = lyrics_data.get("lyrics")
                if isinstance(lyrics_text, str):
                    lyrics_lines = lyrics_text.splitlines()
        except Exception:
            lyrics_lines = None

    return {
        "artist": artists[0].get("name") if artists else None,
        "lyricsLines": lyrics_lines,
        "thumbnail": thumbnails[-1].get("url") if thumbnails else None,
        "title": song.get("title"),
        "videoId": video_id,
    }


@app.get("/search")
def search(
    q: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=10),
):
    if not q:
        return JSONResponse(status_code=400, content={"error": "Missing query"})

    try:
        yt = get_ytmusic()
        results = yt.search(q, filter="songs")

        if not results:
            return JSONResponse(status_code=404, content={"error": "No song found"})

        songs_to_process = results[:limit]
        max_workers = min(4, len(songs_to_process))

        if max_workers <= 1:
            songs = [build_song_result(song) for song in songs_to_process]
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                songs = list(executor.map(build_song_result, songs_to_process))

        return songs

    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/song")
def song(videoId: str | None = Query(default=None)):
    if not videoId:
        return JSONResponse(status_code=400, content={"error": "Missing videoId"})

    try:
        yt = get_ytmusic()
        watch = yt.get_watch_playlist(videoId)
        track = (watch.get("tracks") or [{}])[0]
        artists = track.get("artists") or [{}]

        return {
            "videoId": videoId,
            "title": track.get("title"),
            "artist": artists[0].get("name"),
            "lyricsId": watch.get("lyrics"),
        }
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/lyrics")
def lyrics(videoId: str | None = Query(default=None)):
    if not videoId:
        return JSONResponse(status_code=400, content={"error": "Missing videoId"})

    try:
        yt = get_ytmusic()
        watch = yt.get_watch_playlist(videoId)
        browse_id = watch.get("lyrics")

        if not browse_id:
            return {"lyricsLines": None}

        lyrics_data = yt.get_lyrics(browse_id)
        lyrics_text = lyrics_data.get("lyrics")

        lyrics_lines = None
        if isinstance(lyrics_text, str):
            lyrics_lines = lyrics_text.splitlines()

        return {
            "lyricsLines": lyrics_lines,
            "source": lyrics_data.get("source"),
        }

    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/")
def home():
    return {"status": "API running - Api by Varad"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
