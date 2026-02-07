import os
import time
import json
import struct
import hmac
import hashlib
import requests
from spotify_exception import SpotifyException


class Spotify:
    def __init__(self, sp_dc):
        self.token_url = "https://open.spotify.com/api/token"
        self.lyrics_url = "https://spclient.wg.spotify.com/color-lyrics/v2/track/"
        self.server_time_url = "https://open.spotify.com/api/server-time"
        self.secret_key_url = "https://github.com/xyloflake/spot-secrets-go/blob/main/secrets/secretDict.json?raw=true"
        self.sp_dc = sp_dc
        self.cache_file = "./spotify_token.json"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": "https://open.spotify.com/",
                "Origin": "https://open.spotify.com/",
            }
        )

    def _get_latest_secret_key_version(self):
        try:
            response = self.session.get(self.secret_key_url)
            response.raise_for_status()
            secrets_data = response.json()
        except Exception as e:
            raise SpotifyException(f"Failed to fetch secrets: {e}")

        version = str(max(secrets_data.keys(), key=int))
        original_secret = secrets_data[version]

        if not isinstance(original_secret, list):
            raise SpotifyException("The original secret must be an array of integers.")

        transformed = []
        for i, char in enumerate(original_secret):
            transformed.append(char ^ ((i % 33) + 9))

        secret_str = "".join(str(x) for x in transformed)
        return secret_str.encode("utf-8"), version

    def generate_totp(self, server_time_seconds, secret):
        period = 30
        digits = 6

        counter = int(server_time_seconds / period)
        counter_bytes = struct.pack(">Q", counter)

        hmac_result = hmac.new(secret, counter_bytes, hashlib.sha1).digest()

        offset = hmac_result[-1] & 0x0F
        binary = (
            (hmac_result[offset] & 0x7F) << 24
            | (hmac_result[offset + 1] & 0xFF) << 16
            | (hmac_result[offset + 2] & 0xFF) << 8
            | (hmac_result[offset + 3] & 0xFF)
        )

        code = binary % (10**digits)
        return str(code).zfill(digits)

    def get_server_time_params(self):
        try:
            response = self.session.get(self.server_time_url, verify=False)
            if not response.ok:
                raise SpotifyException(f"Failed to fetch server time: {response.text}")

            server_time_data = response.json()
            server_time_seconds = server_time_data.get("serverTime")
            if server_time_seconds is None:
                raise SpotifyException("Invalid server time response")

            secret, version = self._get_latest_secret_key_version()
            totp = self.generate_totp(server_time_seconds, secret)

            timestamp = int(time.time())
            params = {
                "reason": "transport",
                "productType": "web-player",
                "totp": totp,
                "totpVer": version,
                "ts": str(timestamp),
            }
            return params
        except Exception as e:
            if isinstance(e, SpotifyException):
                raise e
            raise SpotifyException(str(e))

    def get_token(self):
        if not self.sp_dc:
            raise SpotifyException("Please set SP_DC as an environmental variable.")

        try:
            params = self.get_server_time_params()
            headers = {"Cookie": f"sp_dc={self.sp_dc}"}

            resp = self.session.get(
                self.token_url,
                params=params,
                headers=headers,
                timeout=600,
                verify=False,
                allow_redirects=False,
            )

            token_json = resp.json()
            if token_json.get("isAnonymous"):
                raise SpotifyException(
                    "The SP_DC set seems to be invalid, please correct it!"
                )

            with open(self.cache_file, "w") as f:
                json.dump(token_json, f)

        except Exception as e:
            if isinstance(e, SpotifyException):
                raise e
            raise SpotifyException(str(e))

    def check_token_expire(self):
        check = os.path.exists(self.cache_file)
        timeleft = 0
        timenow = int(time.time() * 1000)

        if check:
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    timeleft = data.get("accessTokenExpirationTimestampMs", 0)
            except Exception:
                check = False

        if not check or timeleft < timenow:
            self.get_token()

    def get_lyrics(self, track_id):
        self.check_token_expire()

        try:
            with open(self.cache_file, "r") as f:
                token_data = json.load(f)
                token = token_data.get("accessToken")

            formatted_url = f"{self.lyrics_url}{track_id}?format=json&market=from_token"
            headers = {"App-platform": "WebPlayer", "Authorization": f"Bearer {token}"}

            response = self.session.get(formatted_url, headers=headers)

            if response.status_code == 429:
                raise SpotifyException(
                    "Rate limited by Spotify. Please try again later.", 429
                )
            elif response.status_code == 404:
                raise SpotifyException(
                    "Lyrics for this track were not found on Spotify.", 404
                )
            elif response.status_code >= 400:
                raise SpotifyException(
                    f"Spotify API error (HTTP {response.status_code})",
                    response.status_code,
                )

            json_res = response.json()
            if not json_res or "lyrics" not in json_res:
                raise SpotifyException("Spotify returned an invalid response.")

            return json_res
        except FileNotFoundError:
            self.get_token()
            return self.get_lyrics(track_id)
        except Exception as e:
            if isinstance(e, SpotifyException):
                raise e
            raise SpotifyException(str(e))

    def get_lrc_lyrics(self, lyrics):
        lrc = []
        for line in lyrics:
            lrc_time = self.format_ms(line["startTimeMs"])
            lrc.append({"timeTag": lrc_time, "words": line["words"]})
        return lrc

    def get_srt_lyrics(self, lyrics):
        srt = []
        for i in range(1, len(lyrics)):
            srt_time = self.format_srt(lyrics[i - 1]["startTimeMs"])
            srt_end_time = self.format_srt(lyrics[i]["startTimeMs"])
            srt.append(
                {
                    "index": i,
                    "startTime": srt_time,
                    "endTime": srt_end_time,
                    "words": lyrics[i - 1]["words"],
                }
            )
        return srt

    def get_raw_lyrics(self, lyrics):
        raw = ""
        for line in lyrics:
            raw += line["words"] + "\n"
        return raw

    def format_ms(self, milliseconds):
        milliseconds = int(milliseconds)
        total_seconds = milliseconds // 1000
        mins = total_seconds // 60
        secs = total_seconds % 60
        hundredths = (milliseconds % 1000) // 10
        return f"{mins:02d}:{secs:02d}.{hundredths:02d}"

    def format_srt(self, milliseconds):
        milliseconds = int(milliseconds)
        hours = milliseconds // 3600000
        rem = milliseconds % 3600000
        mins = rem // 60000
        rem = rem % 60000
        secs = rem // 1000
        ms = rem % 1000
        return f"{hours:02d}:{mins:02d}:{secs:02d},{ms:03d}"
