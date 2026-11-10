# TYDL

**TYDL (Termux YouTube Downloader)** es un descargador de línea de comandos para Android mediante Termux. Recibe enlaces desde `termux-url-opener` y ofrece una interfaz interactiva basada en Rich.

> **Estado del proyecto:** en desarrollo. La instalación, las descargas reales y la integración con Spotify deben probarse en Termux antes de considerar una versión estable.

## Características

- Recibe enlaces desde el mecanismo de compartir de Android/Termux.
- Detecta enlaces de YouTube, Spotify, Dailymotion y TikTok.
- Permite descargar audio en MP3 y video en MP4 mediante `yt-dlp` y FFmpeg.
- Muestra información del contenido y opciones de resolución disponibles.
- Usa Spotipy para consultar canciones y playlists de Spotify; busca cada canción en YouTube y descarga el audio con `yt-dlp`.
- Incluye historial, configuración y una opción de reparación de dependencias.
- Verifica que el archivo final exista y no esté vacío antes de informar que la descarga terminó correctamente.

La disponibilidad y el funcionamiento de cada plataforma pueden cambiar. Spotify se utiliza para consultar metadatos; la descarga se realiza desde resultados encontrados en YouTube, no desde Spotify.

## Requisitos

- Android con [Termux](https://github.com/termux/termux-app) instalado. Se recomienda instalar Termux desde una fuente mantenida, como F-Droid o GitHub, y no mezclar fuentes de instalación.
- Python 3.
- Git.
- curl.
- FFmpeg.
- Una conexión a Internet.
- Para la integración Spotify: una aplicación creada en el [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) con Client ID y Client Secret.

El Bootstrap puede instalar `python`, `git`, `curl` y `ffmpeg` mediante `pkg` si faltan. Las dependencias Python se instalan desde `requirements.txt`.

## Dependencias Python

```text
spotipy
yt-dlp
rich
```

Instalación manual de dependencias (opcional):

```bash
python -m pip install -r requirements.txt
```

En el flujo normal, el Bootstrap crea y utiliza un entorno virtual independiente en `~/.milux/venvs/tydl`.

## Instalación en Termux

El Bootstrap de este repositorio está pensado para guardarse en:

```text
~/bin/termux-url-opener
```

1. Instala Termux y abre una sesión.
2. Instala las herramientas necesarias:

   ```bash
   pkg update
   pkg install python git curl ffmpeg
   ```

3. Prepara el acceso al almacenamiento compartido de Android:

   ```bash
   termux-setup-storage
   ```

4. Crea el directorio del Bootstrap y coloca allí el archivo `termux-url-opener` de este repositorio:

   ```bash
   mkdir -p ~/bin
   chmod 700 ~/bin/termux-url-opener
   bash -n ~/bin/termux-url-opener
   ```

5. Ejecuta el Bootstrap con una URL compartida o desde Termux:

   ```bash
   bash ~/bin/termux-url-opener "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

   En el primer uso, el Bootstrap clona el repositorio en `~/.milux/ydl`, crea el entorno virtual e instala las dependencias Python.

> La integración con el menú Compartir de Android depende de la configuración de Termux y de la aplicación que envía el enlace. Si el sistema no invoca el archivo automáticamente, ejecuta el comando anterior manualmente.

## Configuración de Spotify

1. Crea una aplicación en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Copia su **Client ID** y **Client Secret**.
3. Crea el archivo privado `~/.milux/spotify.json` en Termux:

   ```bash
   mkdir -p ~/.milux
   nano ~/.milux/spotify.json
   ```

4. Coloca las credenciales con este formato:

   ```json
   {
     "client_id": "TU_CLIENT_ID",
     "client_secret": "TU_CLIENT_SECRET"
   }
   ```

5. Guarda el archivo y protege sus permisos:

   ```bash
   chmod 600 ~/.milux/spotify.json
   ```

**No publiques `spotify.json`, Client ID/Secret, tokens ni otros datos privados en GitHub.** El archivo de credenciales no forma parte del repositorio.

## Uso

Comparte una URL con TYDL o ejecuta el Bootstrap pasando la URL como argumento:

```bash
bash ~/bin/termux-url-opener "URL"
```

Para iniciar el menú administrativo de TYDL directamente:

```bash
~/.milux/venvs/tydl/bin/python ~/.milux/ydl/main.py
```

Opciones de línea de comandos disponibles en `main.py`:

```bash
python main.py --help
python main.py --repair
python main.py --about
python main.py --history
python main.py --config
python main.py --audio "URL"
python main.py --video 720 "URL"
```

Estas opciones se ejecutan usando el Python del entorno virtual cuando TYDL ya está instalado.

## Actualización manual

La actualización se realiza desde el Bootstrap; `main.py` no administra actualizaciones.

```bash
bash ~/bin/termux-url-opener --update
```

El Bootstrap actualiza el repositorio local con `git pull --ff-only` y vuelve a instalar las dependencias declaradas en `requirements.txt`.

## Rutas y archivos locales

| Elemento | Ubicación |
|---|---|
| Aplicación | `~/.milux/ydl` |
| Bootstrap | `~/bin/termux-url-opener` |
| Entorno virtual | `~/.milux/venvs/tydl` |
| Configuración general | `~/.milux/config.json` |
| Credenciales Spotify | `~/.milux/spotify.json` |
| Historial | `~/.milux/history.json` |
| Registro de errores | `~/.milux/ydl.log` |

Por defecto, las descargas se guardan en `Youtube` dentro del almacenamiento compartido (`~/storage/shared/Youtube`) cuando está disponible; de lo contrario, se utiliza `/sdcard/Youtube`. Las descargas asociadas a Spotify se guardan en la subcarpeta `spotify`. Las rutas pueden ajustarse desde la configuración de TYDL.

## Estructura del repositorio

```text
TYDL/
├── main.py
├── spotify.py
├── requirements.txt
├── termux-url-opener
└── README.md
```

## Desarrollo y publicación

Antes de publicar cambios:

1. Comprueba la sintaxis de Python:

   ```bash
   python -m py_compile main.py spotify.py
   ```

2. Comprueba la sintaxis Bash del Bootstrap:

   ```bash
   bash -n termux-url-opener
   ```

3. Prueba en Termux una instalación limpia, una descarga directa de YouTube, una canción de Spotify, una playlist y la actualización manual.
4. No subas credenciales, archivos de configuración personales, historial, descargas, entornos virtuales ni registros.

## Aviso

Este proyecto es una herramienta técnica. El usuario es responsable de respetar los derechos de autor, los términos de servicio de las plataformas y las leyes aplicables. Descarga únicamente contenido para el que tenga autorización.
