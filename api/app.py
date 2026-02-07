from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from spotify import Spotify
from spotify_exception import SpotifyException
from flask_cors import CORS

load_dotenv()


app = Flask(__name__)
CORS(app)


@app.route("/api/", methods=["GET"])
def get_lyrics():
    trackid = request.args.get("trackid")
    url = request.args.get("url")
    fmt = request.args.get("format")

    if not trackid and not url:
        return (
            jsonify(
                {
                    "error": True,
                    "message": "url or trackid parameter is required!",
                    "usage": "https://github.com/akashrchandran/spotify-lyrics-api",
                }
            ),
            400,
        )

    if url:
        import re

        match = re.search(r"track[/:]+([A-Za-z0-9]+)", url)
        if match:
            trackid = match.group(1)
        else:
            pass

    try:
        sp_dc = os.environ.get("SP_DC")
        print(sp_dc)
        if not sp_dc:
            pass

        spotify = Spotify(sp_dc)
        lyrics_data = spotify.get_lyrics(trackid)

        return build_response(spotify, lyrics_data, fmt)

    except SpotifyException as e:
        status_code = (
            e.args[1] if len(e.args) > 1 and isinstance(e.args[1], int) else 500
        )
        if status_code < 100 or status_code > 599:
            status_code = 500

        return jsonify({"error": True, "message": str(e)}), status_code
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500


def build_response(spotify: Spotify, lyrics_data: dict, fmt: str):
    lyrics_lines = lyrics_data["lyrics"]["lines"]

    if fmt == "lrc":
        lines = spotify.get_lrc_lyrics(lyrics_lines)
    elif fmt == "srt":
        lines = spotify.get_srt_lyrics(lyrics_lines)
    elif fmt == "raw":
        lines = spotify.get_raw_lyrics(lyrics_lines)
    else:
        lines = lyrics_lines

    return jsonify(
        {"error": False, "syncType": lyrics_data["lyrics"]["syncType"], "lines": lines}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
