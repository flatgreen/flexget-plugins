from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.template import RenderError
from flexget.utils.pathscrub import pathscrub
import os
import importlib
import tempfile
import shutil
import uuid

logger = logger.bind(name="youtubedl")

# Inspiration :
# https://github.com/z00nx/flexget-plugins/blob/master/youtubedl.py
# see discussion : https://github.com/Flexget/Flexget/pull/65


class PluginYoutubeDL(object):
    """
    Download videos using youtube-dl or yt-dlp

    This plugin requires the 'youtube-dl' or 'yt-dlp' Python module.
    To install the Python module run:
    'pip install youtube-dl' or 'pip install yt-dlp

    Web site :
    https://github.com/rg3/youtube-dl
    https://github.com/yt-dlp/yt-dlp

    Examples with simple configuration ::

    youtubedl: <path>   Destination folder path

    Advanced usages with properties configuration:

    ytdl_name:      youtube downloader: youtube-dl or yt-dlp (default)
    format:         Video format code (default : ytdl downloader default)
    template:       Output filename template (default: '%(title)s-%(id)s.%(ext)s')
    path:           Destination path (can be use with 'Set' plugin) - Required
    others_options:  all parameters youtube-dl|yt-dlp can accept
                    https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L141
                    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L197
                    Pay attention to the differences between these two softwares.

    'template' and 'path' support Jinja2 templating on the input entry

    Examples::

    youtubedl:
        ytdl_name: yt-dlp
        template: {{ title }}.%(ext)s
        path: ~/downloads/

    youtubedl:
        path: ~/dowload/
        format: '160/18'
        other_options:
            writeinfojson: true

    Example with yt-dlp, extract audio::

    youtubedl:
        path: ~/dowload/
        format: bestaudio*
        other_options:
          postprocessors:
            - key: FFmpegExtractAudio
              preferredcodec: best
    """

    schema = {
        "oneOf": [
            {"type": "string", "format": "path"},
            {
                "type": "object",
                "properties": {
                    "ytdl_name": {"type": "string"},
                    "format": {"type": "string"},
                    "template": {"type": "string"},
                    "path": {"type": "string", "format": "path"},
                    "other_options": {"type": "object"},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        ]
    }

    ytdl_name_to_module = {"youtube-dl": "youtube_dl", "yt-dlp": "yt_dlp"}

    def prepare_config(self, config):
        if isinstance(config, str):
            config = {"path": config}
        config.setdefault("template", "%(title)s-%(id)s.%(ext)s")
        config.setdefault("ytdl_name", "yt-dlp")

        # import the yt-dlp or youtube-dl module
        ytdl = config["ytdl_name"]
        try:
            self.ytdl_module_name = self.ytdl_name_to_module[ytdl]
        except KeyError as e:
            raise plugin.PluginError(
                "Invalid `ytdl_name` in configuration. KeyError: %s. Choose: `yt-dlp` or `youtube-dl`."
                % e
            )
        try:
            self.ytdl_module = importlib.import_module(self.ytdl_module_name)
            logger.debug("importing YoutubeDL module: %s" % self.ytdl_module)
        except ImportError as e:
            raise plugin.PluginError(
                "youtube downloader module required. ImportError: %s" % e
            )
        logger.verbose("Plugin YoutubeDL will use: %s" % ytdl)

        return config

    def prepare_path(self, entry, config):
        # with 'Set' plugin
        path = entry.get("path", config.get("path"))
        if not isinstance(path, str):
            raise plugin.PluginError("Invalid `path` in entry `%s`" % entry["title"])
        try:
            path = os.path.expanduser(entry.render(path))
        except RenderError as e:
            entry.fail("Could not set path. Error during string replacement: %s" % e)
            return
        return path

    def prepare_params(self, config, outtmpl):
        # ytdl options by default
        params = {
            "quiet": True,
            "outtmpl": outtmpl,
            "logger": logger,
            "noprogress": True,
        }
        # add config to params
        if "format" in config:
            if config["format"]:
                params.update({"format": config["format"]})
        if config.get("other_options"):
            params.update(config["other_options"])
        logger.debug(params)
        return params

    def on_task_output(self, task, config):
        if task.options.learn:
            return
        config = self.prepare_config(config)
        for entry in task.accepted:
            # path is the final path
            path = self.prepare_path(entry, config)
            
            # create temp directory in this path
            tmpdirname = os.path.join(path, str(uuid.uuid4()))
            logger.debug('dl tmp dir : %s' % tmpdirname)
            os.makedirs(tmpdirname)
            shutil.copymode(path, tmpdirname)

            # prepare outtmpl
            try:
                template = pathscrub(entry.render(config["template"])).replace('/', '_')
                outtmpl = os.path.join(tmpdirname, template)
                logger.debug("Output full template: %s" % outtmpl)
            except RenderError as e:
                logger.error("Error setting output file: %s" % e)
                # TODO remove tmpdirname ? mieux organiser
                entry.fail("Error setting output file: %s" % e)

            # ytdl options
            params = self.prepare_params(config, outtmpl)

            if task.options.test:
                logger.info("Would download `{}` in `{}`", entry["title"], path)
            else:
                logger.info("Downloading `{}` in `{}`", entry["title"], path)
                try:
                    with self.ytdl_module.YoutubeDL(params) as ydl:
                        ydl.download([entry["url"]])
                except (
                    self.ytdl_module.utils.ExtractorError,
                    self.ytdl_module.utils.DownloadError,
                ) as e:
                    entry.fail("YoutubeDL downloader error: %s" % e)
                except Exception as e:
                    entry.fail("YoutubeDL downloader failed. Error message: %s" % e)
                else:
                    # copy all files from tmpdirname to path
                    logger.debug("move from {} to {}", tmpdirname, path)
                    # shutil.copytree(tmpdirname, path, dirs_exist_ok=True)
                    # TODO nettoyer, sur rasp c'est copytree
                    all_files = os.listdir(tmpdirname)
                    for file_name in all_files:
                        src = os.path.join(tmpdirname, file_name)
                        dst = os.path.join(path, file_name)
                        shutil.copy2(src, dst)
                        # shutil.copymode(src, dst)
                finally:
                    logger.debug("remove ytdl tmp dir")
                    shutil.rmtree(tmpdirname)


@event("plugin.register")
def register_plugin():
    plugin.register(PluginYoutubeDL, "youtubedl", api_ver=2)
