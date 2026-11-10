from pathlib import Path
import json
import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


CONFIG_FILE = (
    Path.home()
    / ".milux"
    / "spotify.json"
)


def load_config():

    if not CONFIG_FILE.exists():

        raise RuntimeError(
            "No existe ~/.milux/spotify.json"
        )

    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            config = json.load(file)

    except Exception as error:

        raise RuntimeError(
            f"No se pudo leer la configuración: {error}"
        )

    client_id = config.get(
        "client_id"
    )

    client_secret = config.get(
        "client_secret"
    )

    if not client_id or not client_secret:

        raise RuntimeError(
            "Faltan client_id o client_secret."
        )

    return (
        client_id,
        client_secret,
    )


def search_youtube(
    track,
    ytdlp_module,
):

    query = build_search_query(
        track
    )

    search = (
        f"ytsearch1:{query}"
    )

    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }

    with ytdlp_module.YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            search,
            download=False,
        )

    if not info:

        return None

    entries = info.get(
        "entries",
        [],
    )

    if not entries:

        return None

    result = entries[0]

    video_url = result.get("webpage_url") or result.get("url")

    if not video_url:
        return None

    if not str(video_url).startswith(("http://", "https://")):
        video_url = f"https://www.youtube.com/watch?v={video_url}"

    return {
        "url": video_url,
        "title": result.get(
            "title",
            "",
        ),
        "duration": result.get(
            "duration"
        ),
        "query": query,
    }


def get_client():

    client_id, client_secret = (
        load_config()
    )

    auth_manager = (
        SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
    )

    return spotipy.Spotify(
        auth_manager=auth_manager
    )


def build_search_query(track):

    artist = track.get(
        "artist",
        "",
    )

    title = track.get(
        "title",
        "",
    )

    return (
        f"{artist} - {title}"
    )

def detect_type(url):

    if "/track/" in url:

        return "track"

    if "/playlist/" in url:

        return "playlist"

    return None


def clean_url(url):

    # Elimina ?si=..., ?utm_..., etc.
    return url.split("?")[0].strip()


def get_track(url):

    spotify = get_client()

    url = clean_url(url)

    data = spotify.track(url)

    if not data:

        return None

    artists = ", ".join(
        artist["name"]
        for artist in data.get(
            "artists",
            [],
        )
    )

    return {
        "type": "track",
        "id": data.get("id"),
        "title": data.get(
            "name",
            "Unknown",
        ),
        "artist": artists,
        "album": (
            data.get("album", {})
            .get(
                "name",
                "",
            )
        ),
        "url": url,
    }


def get_playlist(url):

    spotify = get_client()

    url = clean_url(url)

    playlist = spotify.playlist(
        url,
        fields=(
            "id,name,description,"
            "tracks.total,"
            "tracks.items"
        ),
    )

    if not playlist:

        return None

    tracks = []

    items = playlist.get(
        "tracks",
        {}
    ).get(
        "items",
        []
    )

    for item in items:

        track = item.get(
            "track"
        )

        if not track:

            continue

        # Puede haber episodios u otros
        # elementos que no sean tracks.
        if track.get(
            "type"
        ) != "track":

            continue

        artists = ", ".join(
            artist["name"]
            for artist in track.get(
                "artists",
                [],
            )
        )

        tracks.append(
            {
                "id": track.get(
                    "id"
                ),
                "title": track.get(
                    "name",
                    "Unknown",
                ),
                "artist": artists,
                "album": (
                    track.get(
                        "album",
                        {},
                    ).get(
                        "name",
                        "",
                    )
                ),
            }
        )

    # Spotify puede devolver páginas.
    while playlist.get(
        "tracks",
        {}
    ).get(
        "next"
    ):

        playlist["tracks"] = (
            spotify.next(
                playlist["tracks"]
            )
        )

        for item in playlist[
            "tracks"
        ].get(
            "items",
            [],
        ):

            track = item.get(
                "track"
            )

            if not track:
                continue

            if track.get(
                "type"
            ) != "track":
                continue

            artists = ", ".join(
                artist["name"]
                for artist in track.get(
                    "artists",
                    [],
                )
            )

            tracks.append(
                {
                    "id": track.get(
                        "id"
                    ),
                    "title": track.get(
                        "name",
                        "Unknown",
                    ),
                    "artist": artists,
                    "album": (
                        track.get(
                            "album",
                            {},
                        ).get(
                            "name",
                            "",
                        )
                    ),
                }
            )

    return {
        "type": "playlist",
        "id": playlist.get(
            "id"
        ),
        "name": playlist.get(
            "name",
            "Spotify Playlist",
        ),
        "description": playlist.get(
            "description"
        ),
        "tracks": tracks,
        "url": url,
    }


def resolve(url):

    url = clean_url(url)

    resource_type = detect_type(
        url
    )

    if resource_type == "track":

        return get_track(url)

    if resource_type == "playlist":

        return get_playlist(url)

    raise ValueError(
        "La URL no parece ser "
        "un track o playlist de Spotify."
    )
