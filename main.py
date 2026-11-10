#!/usr/bin/env python3

"""
============================================================
TYDL 2.0
============================================================

by Milux

Motor:
    yt-dlp
    ffmpeg
    Spotipy

Características:
    • URL recibida desde termux-url-opener
    • Detección automática de plataforma
    • Información del contenido
    • Formatos reales disponibles
    • Resolución
    • FPS
    • Codec
    • Audio/video
    • Tamaño estimado
    • MP3
    • Video
    • Menú persistente
    • Reparar
    • Acerca de
    • Salir
    • Historial
    • Configuración
    • Múltiples descargas durante una sesión

============================================================
"""

from __future__ import annotations

import spotify
import argparse
import json
import os
import shutil
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

import yt_dlp

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from rich import box


# ============================================================
# INFORMACIÓN
# ============================================================

APP_NAME = "TYDL"
VERSION = "2.0.0"
AUTHOR = "Milux"

# ============================================================
# RUTAS
# ============================================================

HOME = Path.home()

APP_DIR = HOME / ".milux"
CONFIG_FILE = APP_DIR / "config.json"
HISTORY_FILE = APP_DIR / "history.json"
LOG_FILE = APP_DIR / "ydl.log"

APP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# STORAGE
# ============================================================

STORAGE = HOME / "storage" / "shared"

if STORAGE.exists():
    DOWNLOAD_DIR = STORAGE / "Youtube"
else:
    DOWNLOAD_DIR = Path("/sdcard/Youtube")

SPOTIFY_DIR = DOWNLOAD_DIR / "spotify"


# ============================================================
# CONFIGURACIÓN
# ============================================================

DEFAULT_CONFIG = {

    "download_dir": str(DOWNLOAD_DIR),

    "spotify_dir": str(SPOTIFY_DIR),

    "audio_format": "mp3",

    "audio_quality": "192",

    "video_format": "mp4",

    "overwrite": False,

    "no_playlist": True,

    "history": True,
}


def load_config():

    if not CONFIG_FILE.exists():

        save_config(
            DEFAULT_CONFIG.copy()
        )

        return DEFAULT_CONFIG.copy()

    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        config = DEFAULT_CONFIG.copy()
        config.update(data)

        return config

    except Exception:

        return DEFAULT_CONFIG.copy()


def save_config(config):

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=4,
            ensure_ascii=False,
        )


CONFIG = load_config()


# ============================================================
# CONSOLA
# ============================================================

console = Console()


def clear():

    os.system("clear")


def pause():

    console.input(
        "\n[dim]ENTER para continuar...[/dim]"
    )


def command_exists(command):

    return shutil.which(command) is not None


def ensure_directory(path):

    Path(path).mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# LOG
# ============================================================

def log(message):

    try:

        with open(
            LOG_FILE,
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                f"{message}\n"
            )

    except Exception:
        pass


# ============================================================
# HISTORIAL
# ============================================================

def load_history():

    if not HISTORY_FILE.exists():
        return []

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception:

        return []


def add_history(
    url,
    title,
    platform,
    media_type,
    resolution="",
):

    if not CONFIG["history"]:
        return

    history = load_history()

    history.append(
        {
            "date":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "title":
                title,

            "url":
                url,

            "platform":
                platform,

            "type":
                media_type,

            "resolution":
                resolution,
        }
    )

    history = history[-500:]

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                history,
                file,
                indent=4,
                ensure_ascii=False,
            )

    except Exception as error:

        log(
            f"Error historial: {error}"
        )


# ============================================================
# HEADER
# ============================================================

def header():

    clear()

    console.print(
        Panel.fit(
            "[bold cyan]Y D L[/bold cyan]"
            " [white]-[/white] "
            "[bold cyan]D O W N L O A D E R[/bold cyan]\n"
            "[dim]YouTube • Spotify • Dailymotion • TikTok[/dim]\n\n"
            "[yellow]by Milux[/yellow]",

            title=(
                f"[bold white]"
                f"{APP_NAME}"
                f"[/bold white]"
            ),

            subtitle=f"v{VERSION}",

            border_style="cyan",
        )
    )


# ============================================================
# PLATAFORMA
# ============================================================

def detect_platform(url):

    value = url.lower()

    if (
        "youtube.com" in value
        or "youtu.be" in value
    ):
        return "YouTube"

    if "spotify.com" in value:
        return "Spotify"

    if (
        "dailymotion.com" in value
        or "dai.ly" in value
    ):
        return "Dailymotion"

    if (
        "tiktok.com" in value
        or "vm.tiktok.com" in value
    ):
        return "TikTok"

    return "Desconocido"


# ============================================================
# TAMAÑO
# ============================================================

def human_size(size):

    if not size:
        return "N/D"

    try:

        size = float(size)

    except (
        TypeError,
        ValueError,
    ):

        return "N/D"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    for unit in units:

        if size < 1024:

            return f"{size:.1f} {unit}"

        size /= 1024

    return f"{size:.1f} PB"


# ============================================================
# DURACIÓN
# ============================================================

def format_duration(seconds):

    if not seconds:
        return "N/D"

    try:

        seconds = int(seconds)

    except (
        TypeError,
        ValueError,
    ):

        return "N/D"

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    secs = seconds % 60

    if hours:

        return (
            f"{hours}:"
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    return (
        f"{minutes}:"
        f"{secs:02d}"
    )


# ============================================================
# INFORMACIÓN
# ============================================================

def extract_info(url):

    options = {

        "quiet": True,

        "no_warnings": True,

        "skip_download": True,

        "noplaylist":
            CONFIG["no_playlist"],
    }

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            return ydl.extract_info(
                url,
                download=False,
            )

    except Exception as error:

        log(
            f"Error obteniendo info: {error}"
        )

        console.print(
            Panel(
                str(error),
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )

        return None

# ============================================================
# SPINNER
# ============================================================

def extract_info_with_spinner(url):

    with console.status(
        "[bold cyan]⠋ Analizando formatos disponibles...[/bold cyan]",
        spinner="dots",
    ):

        return extract_info(url)

# ============================================================
# INFORMACIÓN DEL VIDEO
# ============================================================

def show_media_info(info):

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
    )

    table.add_column(
        "Dato",
        style="yellow",
    )

    table.add_column(
        "Informacion",
        style="white",
    )

    table.add_row(
        "Título",
        info.get(
            "title",
            "N/D",
        ),
    )

    table.add_row(
        "Autor",
        info.get(
            "uploader",
            info.get(
                "channel",
                "N/D",
            ),
        ),
    )

    table.add_row(
        "Duración",
        format_duration(
            info.get(
                "duration"
            )
        ),
    )

    table.add_row(
        "Plataforma",
        detect_platform(
            info.get(
                "webpage_url",
                "",
            )
        ),
    )

    console.print(table)


# ============================================================
# FORMATOS
# ============================================================

def get_video_formats(info):

    formats_by_height = {}
    all_formats = info.get("formats", [])

    # Guardar el mejor audio separado para una estimación aproximada.
    audio_formats = [
        fmt for fmt in all_formats
        if fmt.get("vcodec") == "none"
        and fmt.get("acodec") not in (None, "none")
    ]

    best_audio = max(
        audio_formats,
        key=lambda fmt: (
            fmt.get("abr") or 0,
            fmt.get("tbr") or 0,
            fmt.get("filesize") or fmt.get("filesize_approx") or 0,
        ),
        default=None,
    )

    audio_size = (
        (best_audio.get("filesize") or best_audio.get("filesize_approx"))
        if best_audio else None
    )

    for fmt in all_formats:
        height = fmt.get("height")
        if not height or fmt.get("vcodec") in (None, "none"):
            continue

        try:
            height = int(height)
        except (TypeError, ValueError):
            continue

        if height < 144:
            continue

        # Puntuar todos los formatos de la misma resolución y conservar
        # el de mayor calidad, en lugar de aceptar el primero de la lista.
        score = (
            fmt.get("quality") or 0,
            fmt.get("preference") or 0,
            fmt.get("vbr") or 0,
            fmt.get("tbr") or 0,
            fmt.get("fps") or 0,
            fmt.get("filesize") or fmt.get("filesize_approx") or 0,
            1 if fmt.get("acodec") not in (None, "none") else 0,
        )

        current = formats_by_height.get(height)
        if current is None or score > current[0]:
            formats_by_height[height] = (score, fmt)

    results = []
    duration = info.get("duration") or 0

    for height, (_, fmt) in formats_by_height.items():
        video_size = fmt.get("filesize") or fmt.get("filesize_approx")

        if not video_size and fmt.get("tbr") and duration:
            video_size = fmt["tbr"] * 1000 / 8 * duration

        total_size = video_size
        # Si el formato elegido ya incluye audio, no sumar audio separado.
        has_audio = fmt.get("acodec") not in (None, "none")
        if total_size and audio_size and not has_audio:
            total_size += audio_size

        results.append({
            "height": height,
            "ext": "mp4",
            "size": total_size,
        })

    results.sort(key=lambda item: item["height"])
    return results

# ============================================================
# TABLA DE FORMATOS
# ============================================================

def show_formats(info):

    formats = get_video_formats(info)

    table = Table(
        title="Formatos disponibles",
        box=box.ROUNDED,
        border_style="cyan",
    )

    table.add_column(
        "#",
        justify="center",
        style="cyan",
    )

    table.add_column(
        "Tipo",
        style="green",
    )

    table.add_column(
        "Calidad",
        style="yellow",
    )

    table.add_column(
        "Ext",
        justify="center",
    )

    table.add_column(
        "Tamaño",
        justify="right",
    )

    # --------------------------------------------------------
    # MP3
    # --------------------------------------------------------

    table.add_row(
        "1",
        "🎵 Audio",
        "MP3",
        "MP3",
        "—",
    )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    option = 2

    for fmt in formats:

        quality = f'{fmt["height"]}p'

        if fmt["height"] >= 2160:

            quality += " • 4K"

        table.add_row(
            str(option),
            "🎬 Video",
            quality,
            "MP4",
            human_size(
                fmt["size"]
            ),
        )

        option += 1

    console.print(table)

    return formats

# ============================================================
# PROGRESO
# ============================================================

class ProgressHook:

    def __init__(self):

        self.progress = None

        self.task = None

    def __call__(self, data):

        status = data.get(
            "status"
        )

        if status == "downloading":

            downloaded = data.get(
                "downloaded_bytes",
                0,
            )

            total = (
                data.get(
                    "total_bytes"
                )
                or data.get(
                    "total_bytes_estimate"
                )
            )

            if self.progress is None:

                self.progress = Progress(
                    SpinnerColumn(),

                    TextColumn(
                        "[bold cyan]"
                        "{task.description}"
                    ),

                    BarColumn(),

                    DownloadColumn(),

                    TransferSpeedColumn(),

                    TimeRemainingColumn(),
                )

                self.progress.start()

                self.task = (
                    self.progress.add_task(
                        "Descargando",
                        total=total,
                        completed=downloaded,
                    )
                )

            else:

                self.progress.update(
                    self.task,
                    total=total,
                    completed=downloaded,
                )

        elif status == "finished":

            if self.progress:

                self.progress.stop()

                self.progress = None

                self.task = None


# ============================================================
# VERIFICACIÓN DE ARCHIVOS
# ============================================================

def verify_download(info, ydl, directory, expected_ext, started_at):
    """Comprueba que yt-dlp haya dejado un archivo final no vacío."""
    candidates = []

    def collect(data):
        if not isinstance(data, dict):
            return
        for key in ("filepath", "_filename"):
            value = data.get(key)
            if value:
                candidates.append(Path(value))
        for key in ("requested_downloads", "requested_formats"):
            values = data.get(key) or []
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, dict):
                        collect(item)

    collect(info)

    try:
        prepared = Path(ydl.prepare_filename(info))
        candidates.extend([
            prepared,
            prepared.with_suffix(f".{expected_ext}"),
        ])
    except Exception:
        pass

    checked = set()
    for candidate in candidates:
        for path in (candidate, candidate.with_suffix(f".{expected_ext}")):
            try:
                resolved = path.resolve()
                if resolved in checked:
                    continue
                checked.add(resolved)
                if path.is_file() and path.stat().st_size > 0:
                    return path
            except OSError:
                continue

    # Respaldo para versiones de yt-dlp que no devuelven filepath final.
    try:
        recent = [
            path for path in Path(directory).rglob("*")
            if path.is_file()
            and path.stat().st_size > 0
            and path.stat().st_mtime >= started_at - 2
            and path.suffix.lower() == f".{expected_ext}"
        ]
        if recent:
            return max(recent, key=lambda path: path.stat().st_mtime)
    except OSError:
        pass

    return None


# ============================================================
# DESCARGA MP3
# ============================================================

def download_audio(url, title, platform, output_dir=None):

    directory = Path(output_dir or CONFIG["download_dir"])
    ensure_directory(directory)

    console.print("\n[bold cyan]🎵 Preparando MP3...[/bold cyan]\n")
    hook = ProgressHook()
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(directory / "%(title)s.%(ext)s"),
        "noplaylist": CONFIG["no_playlist"],
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "overwrites": CONFIG["overwrite"],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": CONFIG["audio_format"],
            "preferredquality": CONFIG["audio_quality"],
        }],
    }

    started_at = time.time()
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = verify_download(
                info, ydl, directory, CONFIG["audio_format"], started_at
            )

        if not final_file:
            raise RuntimeError(
                "yt-dlp terminó, pero no se encontró el archivo de audio final."
            )

        console.print(
            f"\n[bold green]✓ MP3 descargado correctamente[/bold green]\n"
            f"[dim]{final_file}[/dim]"
        )
        add_history(url, title, platform, "audio")
        return True

    except Exception as error:
        console.print(Panel(
            str(error),
            title="[bold red]Error de descarga[/bold red]",
            border_style="red",
        ))
        log(f"Audio: {error}")
        return False


# ============================================================
# DESCARGA VIDEO
# ============================================================

def download_video(url, title, platform, height):

    directory = Path(CONFIG["download_dir"])
    ensure_directory(directory)
    console.print(
        f"\n[bold cyan]🎬 Preparando {height}p...[/bold cyan]\n"
    )
    hook = ProgressHook()

    # Prioriza el mejor video de esa altura + mejor audio;
    # si no hay streams separados, usa el mejor formato combinado exacto.
    format_selector = (
        f"bestvideo[height={height}]+bestaudio/"
        f"best[height={height}]"
    )

    options = {
        "format": format_selector,
        "outtmpl": str(directory / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "postprocessors": [{
            "key": "FFmpegVideoRemuxer",
            "preferedformat": "mp4",
        }],
        "noplaylist": CONFIG["no_playlist"],
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "overwrites": CONFIG["overwrite"],
    }

    started_at = time.time()
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = verify_download(
                info, ydl, directory, "mp4", started_at
            )

        if not final_file:
            raise RuntimeError(
                "yt-dlp terminó, pero no se encontró el archivo de video final."
            )

        console.print(
            f"\n[bold green]✓ Video descargado correctamente[/bold green]\n"
            f"[dim]{final_file}[/dim]"
        )
        add_history(url, title, platform, "video", f"{height}p")
        return True

    except Exception as error:
        console.print(Panel(
            str(error),
            title="[bold red]Error de descarga[/bold red]",
            border_style="red",
        ))
        log(f"Video: {error}")
        return False

# ============================================================
# SPOTIFY
# ============================================================

def handle_spotify(url):

    try:

        with console.status(
            "[bold green]"
            "⠋ Analizando Spotify..."
            "[/bold green]",
            spinner="dots",
        ):

            data = spotify.resolve(
                url
            )

    except Exception as error:

        console.print(
            Panel(
                str(error),
                title="Spotify",
                border_style="red",
            )
        )

        return

    if not data:

        console.print(
            "[red]No se pudo obtener "
            "la información.[/red]"
        )

        return

    if data["type"] == "track":

        handle_spotify_track(
            data
        )

    elif data["type"] == "playlist":

        handle_spotify_playlist(
            data
        )

def handle_spotify_track(
    track
):

    console.print(
        Panel(
            f"[bold]🎵 {track['title']}[/bold]\n"
            f"👤 {track['artist']}\n"
            f"💿 {track['album']}",
            title="Spotify",
            border_style="green",
        )
    )

    try:
        with console.status(
            "[bold cyan]"
            "⠋ Buscando en YouTube..."
            "[/bold cyan]",
            spinner="dots",
        ):
            result = spotify.search_youtube(track, yt_dlp)
    except Exception as error:
        console.print(Panel(
            str(error),
            title="[bold red]Error buscando en YouTube[/bold red]",
            border_style="red",
        ))
        log(f"Spotify search: {error}")
        return

    if not result or not result.get("url"):

        console.print(
            "[red]"
            "✗ No se encontró "
            "el contenido en YouTube."
            "[/red]"
        )

        return

    console.print(
        Panel(
            f"✓ [bold]{result['title']}[/bold]",
            title="Resultado encontrado",
            border_style="green",
        )
    )

    answer = Prompt.ask(
        "¿Descargar?",
        choices=[
            "s",
            "n",
        ],
        default="s",
    )

    if answer == "s":

        download_audio(
            result["url"],
            track["title"],
            "Spotify",
            output_dir=CONFIG["spotify_dir"],
        )

def handle_spotify_playlist(
    playlist
):

    tracks = playlist.get(
        "tracks",
        [],
    )

    total = len(tracks)

    console.print(
        Panel(
            f"[bold]📀 {playlist['name']}[/bold]\n"
            f"🎵 {total} canciones",
            title="Spotify Playlist",
            border_style="green",
        )
    )

    if total == 0:

        console.print(
            "[yellow]"
            "La playlist está vacía."
            "[/yellow]"
        )

        return

    answer = Prompt.ask(
        "¿Descargar playlist completa?",
        choices=[
            "s",
            "n",
        ],
        default="s",
    )

    if answer != "s":

        return

    console.print()

    completed = 0
    failed = 0

    for index, track in enumerate(
        tracks,
        start=1,
    ):

        console.print(
            f"\n[bold cyan]"
            f"[{index}/{total}] "
            f"{track['artist']} - "
            f"{track['title']}"
            f"[/bold cyan]"
        )

        try:

            with console.status(
                "⠋ Buscando en YouTube...",
                spinner="dots",
            ):

                result = (
                    spotify.search_youtube(
                        track,
                        yt_dlp,
                    )
                )

            if not result:

                console.print(
                    "[red]✗ No encontrado[/red]"
                )

                failed += 1

                continue

            console.print(
                f"[green]✓ Encontrado:[/green] "
                f"{result['title']}"
            )

            success = download_audio(
                result["url"],
                track["title"],
                "Spotify",
                output_dir=CONFIG["spotify_dir"],
            )

            if success:

                completed += 1

            else:

                failed += 1

        except Exception as error:

            console.print(
                f"[red]✗ Error: {error}[/red]"
            )

            failed += 1

    console.print()

    console.print(
        Panel(
            f"✓ Completadas: {completed}\n"
            f"✗ Fallidas: {failed}\n"
            f"🎵 Total: {total}",
            title="Playlist finalizada",
            border_style="cyan",
        )
    )


# ============================================================
# DESCARGA DE URL
# ============================================================

def download_session(url):

    platform = detect_platform(
        url
    )

    if platform == "Desconocido":

        console.print(
            Panel(
                "La URL no pertenece a una "
                "plataforma compatible.",
                title="[red]URL no reconocida[/red]",
                border_style="red",
            )
        )

        pause()

        return

    if platform == "Spotify":

        handle_spotify(url)

        return

    # --------------------------------------------------------
    # ANALIZAR
    # --------------------------------------------------------

    info = extract_info_with_spinner(
    url
)

    if not info:

        pause()

        return

    title = info.get(
        "title",
        "Sin título",
    )

    # --------------------------------------------------------
    # SESIÓN
    # --------------------------------------------------------

    while True:

        header()

        show_media_info(
            info
        )

        console.print()

        formats = show_formats(
            info
        )

        console.print()

        console.print(
            Panel(
                "[cyan][R][/cyan] "
                "🔧 Reparar\n"
                "[cyan][A][/cyan] "
                "ℹ Acerca de\n"
                "[cyan][X][/cyan] "
                "🚪 Salir",
                title="Funciones",
                border_style="cyan",
            )
        )

        option = Prompt.ask(
            "\nTYDL ›"
        ).strip().lower()

        # ----------------------------------------------------
        # SALIR
        # ----------------------------------------------------

        if option == "x":

            return

        # ----------------------------------------------------
        # REPARAR
        # ----------------------------------------------------

        if option == "r":

            repair_ydl()

            continue

        # ----------------------------------------------------
        # ACERCA DE
        # ----------------------------------------------------

        if option == "a":

            about()

            continue

        # ----------------------------------------------------
        # FORMATO
        # ----------------------------------------------------

        try:

            selected = int(
                option
            )

        except ValueError:

            console.print(
                "[red]Opción inválida.[/red]"
            )

            time.sleep(1)

            continue

        # MP3
        if selected == 1:

            success = download_audio(
                url,
                title,
                platform,
            )

            if success:
                return

            pause()
            continue

        # VIDEO
        index = (
            selected - 2
        )

        if (
            index < 0
            or index >= len(formats)
        ):

            console.print(
                "[red]"
                "Formato inválido."
                "[/red]"
            )

            time.sleep(1)

            continue

        height = formats[
            index
        ]["height"]

        success = download_video(
            url,
            title,
            platform,
            height,
        )

        if success:
            return

        pause()


# ============================================================
# REPARAR YDL
# ============================================================

def repair_ydl():

    header()
    console.print(Panel(
        "[bold yellow]Reparación de TYDL[/bold yellow]",
        border_style="yellow",
    ))

    requirements_file = Path(__file__).resolve().with_name("requirements.txt")

    def dependency_status():
        checks = []
        checks.append(("Python", True, sys.version.split()[0]))

        for label, module_name in (
            ("yt-dlp", "yt_dlp"),
            ("Spotipy", "spotipy"),
            ("Rich", "rich"),
        ):
            try:
                module = __import__(module_name)
                version = getattr(module, "__version__", "Instalado")
                checks.append((label, True, str(version)))
            except Exception as error:
                checks.append((label, False, str(error)))

        checks.append((
            "FFmpeg",
            command_exists("ffmpeg"),
            "OK" if command_exists("ffmpeg") else "No encontrado; instalar con pkg install ffmpeg",
        ))
        checks.append((
            "requirements.txt",
            requirements_file.is_file(),
            str(requirements_file) if requirements_file.is_file() else "No encontrado",
        ))

        try:
            ensure_directory(CONFIG["download_dir"])
            ensure_directory(CONFIG["spotify_dir"])
            checks.append(("Directorios", True, "OK"))
        except Exception as error:
            checks.append(("Directorios", False, str(error)))
        return checks

    def show_checks(checks):
        table = Table(box=box.ROUNDED, border_style="cyan")
        table.add_column("Componente")
        table.add_column("Estado")
        table.add_column("Detalle")
        for name, ok, detail in checks:
            table.add_row(
                name,
                "[green]✓ OK[/green]" if ok else "[red]✗ ERROR[/red]",
                detail,
            )
        console.print(table)

    show_checks(dependency_status())

    if Confirm.ask("\n¿Reinstalar las dependencias de requirements.txt?", default=False):
        if not requirements_file.is_file():
            console.print("[red]No se puede reparar: falta requirements.txt.[/red]")
        else:
            result = subprocess.run(
                [
                    sys.executable, "-m", "pip", "install",
                    "--upgrade", "--force-reinstall",
                    "-r", str(requirements_file),
                ],
                check=False,
            )
            if result.returncode == 0:
                console.print("[green]✓ Dependencias Python reinstaladas.[/green]")
            else:
                console.print("[red]✗ Falló la reinstalación de dependencias.[/red]")
                log(f"Repair pip exit code: {result.returncode}")

    if not command_exists("ffmpeg"):
        console.print("\n[yellow]FFmpeg no está instalado.[/yellow]")
        if command_exists("pkg") and Confirm.ask(
            "¿Instalar FFmpeg ahora mediante Termux?", default=True
        ):
            result = subprocess.run(
                ["pkg", "install", "-y", "ffmpeg"],
                check=False,
            )
            if result.returncode == 0 and command_exists("ffmpeg"):
                console.print("[green]✓ FFmpeg instalado correctamente.[/green]")
            else:
                console.print("[red]✗ No se pudo instalar FFmpeg.[/red]")
                log(f"FFmpeg install exit code: {result.returncode}")
        else:
            console.print("[dim]Puedes instalarlo después con: pkg install ffmpeg[/dim]")

    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG.copy())
        console.print("\n[green]✓ Configuración reconstruida.[/green]")

    console.print("\n[bold]Estado después de la reparación:[/bold]")
    show_checks(dependency_status())
    pause()


# ============================================================
# ACERCA DE
# ============================================================

def about():

    header()

    console.print(
        Panel(
            f"""
[bold cyan]{APP_NAME}[/bold cyan]

Versión:
[yellow]{VERSION}[/yellow]

Autor:
[yellow]{AUTHOR}[/yellow]

Motor de descarga:
[green]yt-dlp[/green]

Integración Spotify:
[green]Spotipy + yt-dlp[/green]

Conversión:
[green]FFmpeg[/green]

Interfaz:
[green]Rich[/green]

Plataformas:
• YouTube
• Dailymotion
• TikTok
• Spotify

TYDL 2.0
""",
            title="Acerca de",
            border_style="cyan",
        )
    )

    pause()


# ============================================================
# HISTORIAL
# ============================================================

def show_history():

    header()

    history = load_history()

    if not history:

        console.print(
            Panel(
                "No hay descargas registradas.",
                border_style="yellow",
            )
        )

        pause()

        return

    table = Table(
        title="Historial",
        box=box.ROUNDED,
        border_style="cyan",
    )

    table.add_column(
        "#",
        style="cyan",
    )

    table.add_column(
        "Fecha",
    )

    table.add_column(
        "Plataforma",
    )

    table.add_column(
        "Tipo",
    )

    table.add_column(
        "Calidad",
    )

    table.add_column(
        "Título",
        max_width=40,
    )

    for number, item in enumerate(
        reversed(history[-50:]),
        1,
    ):

        table.add_row(
            str(number),
            item.get(
                "date",
                "",
            ),
            item.get(
                "platform",
                "",
            ),
            item.get(
                "type",
                "",
            ),
            item.get(
                "resolution",
                "",
            ),
            item.get(
                "title",
                "",
            ),
        )

    console.print(
        table
    )

    pause()


# ============================================================
# CONFIGURACIÓN
# ============================================================

def settings():

    while True:

        header()

        table = Table(
            title="Configuración",
            box=box.ROUNDED,
            border_style="cyan",
        )

        table.add_column(
            "#"
        )

        table.add_column(
            "Opción"
        )

        table.add_column(
            "Valor"
        )

        table.add_row(
            "1",
            "Carpeta de descargas",
            CONFIG[
                "download_dir"
            ],
        )

        table.add_row(
            "2",
            "Carpeta Spotify",
            CONFIG[
                "spotify_dir"
            ],
        )

        table.add_row(
            "3",
            "Calidad MP3",
            CONFIG[
                "audio_quality"
            ] + " kbps",
        )

        table.add_row(
            "4",
            "Sobrescribir",
            str(
                CONFIG[
                    "overwrite"
                ]
            ),
        )

        table.add_row(
            "5",
            "No playlist",
            str(
                CONFIG[
                    "no_playlist"
                ]
            ),
        )

        table.add_row(
            "6",
            "Historial",
            str(
                CONFIG[
                    "history"
                ]
            ),
        )

        table.add_row(
            "X",
            "Salir",
            "",
        )

        console.print(
            table
        )

        option = Prompt.ask(
            "TYDL ›"
        ).lower()

        if option == "x":

            return

        elif option == "1":

            CONFIG[
                "download_dir"
            ] = os.path.expanduser(
                Prompt.ask(
                    "Nueva carpeta",
                    default=CONFIG[
                        "download_dir"
                    ],
                )
            )

            save_config(
                CONFIG
            )

        elif option == "2":

            CONFIG[
                "spotify_dir"
            ] = os.path.expanduser(
                Prompt.ask(
                    "Nueva carpeta",
                    default=CONFIG[
                        "spotify_dir"
                    ],
                )
            )

            save_config(
                CONFIG
            )

        elif option == "3":

            quality = Prompt.ask(
                "Calidad MP3",
                default=CONFIG[
                    "audio_quality"
                ],
            )

            if quality in {
                "64",
                "96",
                "128",
                "160",
                "192",
                "256",
                "320",
            }:

                CONFIG[
                    "audio_quality"
                ] = quality

                save_config(
                    CONFIG
                )

        elif option == "4":

            CONFIG[
                "overwrite"
            ] = not CONFIG[
                "overwrite"
            ]

            save_config(
                CONFIG
            )

        elif option == "5":

            CONFIG[
                "no_playlist"
            ] = not CONFIG[
                "no_playlist"
            ]

            save_config(
                CONFIG
            )

        elif option == "6":

            CONFIG[
                "history"
            ] = not CONFIG[
                "history"
            ]

            save_config(
                CONFIG
            )


# ============================================================
# MENÚ ADMINISTRATIVO
# ============================================================

def admin_menu():

    while True:

        header()

        table = Table(
            title="Funciones TYDL",
            box=box.ROUNDED,
            border_style="cyan",
        )

        table.add_column(
            "#",
            style="cyan",
        )

        table.add_column(
            "Función",
            style="yellow",
        )

        table.add_row(
            "R",
            "🔧 Reparar",
        )

        table.add_row(
            "A",
            "ℹ Acerca de",
        )

        table.add_row(
            "H",
            "📜 Historial",
        )

        table.add_row(
            "C",
            "⚙ Configuración",
        )

        table.add_row(
            "X",
            "🚪 Salir",
        )

        console.print(
            table
        )

        option = Prompt.ask(
            "TYDL ›"
        ).lower()

        if option == "r":

            repair_ydl()

        elif option == "a":

            about()

        elif option == "h":

            show_history()

        elif option == "c":

            settings()

        elif option == "x":

            return


# ============================================================
# ARGUMENTOS
# ============================================================

def parser():

    p = argparse.ArgumentParser(
        prog="ydl",
        description="TYDL 2.0",
    )

    p.add_argument(
        "urls",
        nargs="*",
    )

    p.add_argument(
        "--audio",
        action="store_true",
    )

    p.add_argument(
        "--video",
        type=int,
    )

    p.add_argument(
        "--repair",
        action="store_true",
    )

    p.add_argument(
        "--about",
        action="store_true",
    )

    p.add_argument(
        "--history",
        action="store_true",
    )

    p.add_argument(
        "--config",
        action="store_true",
    )

    return p


# ============================================================
# MAIN
# ============================================================

def main():

    args = parser().parse_args()

    # --------------------------------------------------------
    # FUNCIONES DIRECTAS
    # --------------------------------------------------------

    if args.repair:

        repair_ydl()

        return

    if args.about:

        about()

        return

    if args.history:

        show_history()

        return

    if args.config:

        settings()

        return

    # --------------------------------------------------------
    # URL RECIBIDA
    # --------------------------------------------------------

    if args.urls:

        for url in args.urls:

            url = url.strip()

            if not url:
                continue

            # Spotify siempre utiliza Spotipy + búsqueda/descarga con yt-dlp,
            # incluso cuando se invoca TYDL con --audio o --video.
            if detect_platform(url) == "Spotify":
                handle_spotify(url)
                continue

            # Modo directo
            if args.audio:

                info = extract_info(
                    url
                )

                if info:

                    download_audio(
                        url,
                        info.get(
                            "title",
                            "",
                        ),
                        detect_platform(
                            url
                        ),
                    )

                continue

            if args.video:

                info = extract_info(
                    url
                )

                if info:

                    download_video(
                        url,
                        info.get(
                            "title",
                            "",
                        ),
                        detect_platform(
                            url
                        ),
                        args.video,
                    )

                continue

            # Modo normal
            download_session(
                url
            )

        return

    # --------------------------------------------------------
    # SIN URL
    # --------------------------------------------------------

    admin_menu()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        console.print(
            "\n[yellow]"
            "Operación cancelada."
            "[/yellow]"
        )

    except Exception as error:

        console.print(
            Panel(
                str(error),
                title="[bold red]"
                       "Error inesperado"
                       "[/bold red]",
                border_style="red",
            )
        )

        log(
            f"Fatal: {error}"
        )
