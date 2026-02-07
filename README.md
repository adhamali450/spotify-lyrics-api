> [!WARNING]
> This project is probably against Spotify TOS. Use at your own risks.

> [!NOTE]
> This is a Python rewrite of the [original PHP project](https://github.com/akashrchandran/spotify-lyrics-api).

# Quick Start with Docker

The easiest way to run the API is using Docker:

```bash
docker run -d --name spotify-lyrics-api -p 8080:8080 -e SP_DC="your_sp_dc_value_here" spotify-lyrics-api
```

Then access the API at `http://localhost:8080/?trackid=YOUR_TRACK_ID`

# Fetching Lyrics

> For now it only supports track id or link.

## Using GET Requests

> You have to use query paramters to send data

**Available Parameters:**

| Parameter  | Default value | Type   | Description                                                         |
| ---------- | ------------- | ------ | ------------------------------------------------------------------- |
| `trackid ` | None          | String | The trackid from spotify.                                           |
| `url`      | None          | String | The url of the track from spotify.                                  |
| `format`   | `"id3"`       | String | The format of lyrics required. Options: `id3`, `lrc`, `srt`, `raw`. |

> You must specify either **trackid** or **url**, otherwise it will return error.

### Examples

**Using trackid**

```
http://localhost:8080/?trackid=5f8eCNwTlr0RJopE9vQ6mB
```

**Using url**

```
http://localhost:8080/?url=https://open.spotify.com/track/5f8eCNwTlr0RJopE9vQ6mB?autoplay=true
```

response:

```json
{
  "error": false,
  "syncType": "LINE_SYNCED",
  "lines": [
    {
      "startTimeMs": "960",
      "words": "One, two, three, four",
      "syllables": [],
      "endTimeMs": "0"
    },
    {
      "startTimeMs": "4020",
      "words": "Ooh-ooh, ooh-ooh-ooh",
      "syllables": [],
      "endTimeMs": "0"
    }
  ]
}
```

**Changing format to lrc**

```
http://localhost:8080/?trackid=5f8eCNwTlr0RJopE9vQ6mB&format=lrc
```

response:

```json
{
  "error": false,
  "syncType": "LINE_SYNCED",
  "lines": [
    {
      "timeTag": "00:00.96",
      "words": "One, two, three, four"
    },
    {
      "timeTag": "00:04.02",
      "words": "Ooh-ooh, ooh-ooh-ooh"
    }
  ]
}
```

### Responses

> Different Responses given out by the API, are listed here.

If any error occurs the value of the error key will be set to `true` else `false`

```JSON
"error": false //no error occured
```

Most of the lyrics are time synced or have timetags and some aren't time synced or have timetags. To differentiate between synced and unsynced we have key `syncType`.

```JSON
"syncType": "LINE_SYNCED"
```

> Musixmatch supports Line synced and Word synced type of timed lyrics. Line Synced is the timetag is given till which the line is sang and the word synced lyrics time specifed when the word comes up in the song. For now Spotify only supports line synced. Maybe they would support word synced in the future :/.

**LINE Synced**

```JSON
{
    "error": false,
    "syncType": "LINE_SYNCED",
    "lines": [
        {
            "timeTag": "00:00.96",
            "words": "One, two, three, four"
        },
        {
            "timeTag": "00:04.02",
            "words": "Ooh-ooh, ooh-ooh-ooh"
        }
    ]
}
```

**NOT Synced or Unsynced**

> Note the `timeTags` is set to `00:00.00`.

```JSON
{
    "error": false,
    "syncType": "UNSYNCED",
    "lines": [
        {
            "timeTag": "00:00.00",
            "words": "jaane nahin denge tuje"
        },
        {
            "timeTag": "00:00.00",
            "words": "chaahe tujh ko rab bulaa le, hum naa rab se darane waale"
        }
    ]
}
```

### Error Messages

**When trackid and url both are not given** (400 Bad Request)

error response:

```json
{
  "error": true,
  "message": "url or trackid parameter is required!"
}
```

**When no lyrics found on spotify for given track** (404 Not Found)

error response:

```json
{
  "error": true,
  "message": "lyrics for this track is not available on spotify!"
}
```

```python
import os
from src.spotify import Spotify, SpotifyException

sp_dc = os.environ.get("SP_DC")
spotify = Spotify(sp_dc)

try:
    # Get lyrics
    lyrics = spotify.get_lyrics(track_id="1418IuVKQPTYqt7QNJ9RXN")

    print(f"Sync Type: {lyrics['lyrics']['syncType']}")

    for line in lyrics['lyrics']['lines']:
        print(f"[{line['startTimeMs']}] {line['words']}")

    # Check token expiry if needed (handled internally mostly but good to know)
    # spotify.check_token_expire()

except SpotifyException as e:
    print(f"Error: {e}")
```

### Formatting Lyrics

```python
lines = lyrics['lyrics']['lines']

# Get lyrics in LRC format
lrc_lines = spotify.get_lrc_lyrics(lines)

# Get lyrics in SRT format
srt_lines = spotify.get_srt_lyrics(lines)

# Get raw lyrics (plain text)
raw_lines = spotify.get_raw_lyrics(lines)
```

**Finding SP_DC**

You will find the detailed guide [here](https://github.com/akashrchandran/syrics/wiki/Finding-sp_dc).

**Run locally**

> use git to clone the repo to your local machine or you can download the latest [zip](https://github.com/adhamali450/spotify-lyrics-api/archive/refs/heads/main.zip) file and extract it.

_You need to have Python 3.x installed on you machine or your virtual env._

**Enter into the folder via terminal**

```sh
cd spotify-lyrics-api
```

**Set SP_DC token as environment variable temprorily**

```sh
export SP_DC=[token here and remove the square brackets]
```

**Install dependencies**

```sh
pip install -r requirements.txt
```

**Start the server**

```sh
python api/app.py
```

now open your browser and type `localhost:8080` and you should see the program running.

# Credits

• [Akash R Chandran](https://akashrchandran.in)
-> For the original PHP project.

• [Me](https://github.com/adhamali450)
-> For the Python rewrite and future updates.
