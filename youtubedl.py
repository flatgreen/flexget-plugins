from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.template import RenderError
from flexget.utils.pathscrub import pathscrub
import os
import importlib

logger = logger.bind(name='youtubedl')

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


    Configuration:

    ytdl_name:      youtube downloader: youtube-dl or yt-dlp (default: youtube-dl)
    format:         Video format code
    template:       Output filename template (default: '%(title)s-%(id)s.%(ext)s')
    path:           Destination path (can be use with 'Set' plugin)
    other_options:  all parameters youtube-dl|yt-dlp can accept
                    https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L141
                    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L197
                    Pay attention to the differences between these two software.

    'template' and 'path' support Jinja2 templating on the input entry

    Examples::

    youtubedl:
        ytdl_name: yt-dlp
        template: {{ title }}.%(ext)s
        path: ~/downloads/

    youtubedl:
        path: 'E:\--DL--\'
        format: '160/18'
        other_options:
            writeinfojson: true
    """

    schema = {
        'type': 'object',
        'properties': {
            'ytdl_name': {'type': 'string', 'default': 'youtube-dl'},
            'format': {'type': 'string', 'default': ''},
            'template': {'type': 'string', 'default': '%(title)s-%(id)s.%(ext)s'},
            'path': {'type': 'string', 'format': 'path'},
            'other_options': {'type': 'object'}
        },
        'additionalProperties': False
    }

    ytdl_name_to_module = {'youtube-dl': 'youtube_dl', 'yt-dlp': 'yt_dlp'}

    def on_task_start(self, task, config):
        if task.options.learn:
            return
        ytdl = config.get('ytdl_name')
        try:
            self.ytdl_module_name = self.ytdl_name_to_module[ytdl]
        except KeyError as e:
            raise plugin.PluginError('Invalid `ytdl_name` in configuration. KeyError: %s' % e)
        try:
            self.ytdl_module = importlib.import_module(self.ytdl_module_name)
        except ImportError as e:
            logger.debug('Error importing YoutubeDL: %s' % e)
            raise plugin.PluginError('youtube downloader module required. ImportError: %s' % e)
        logger.verbose('Plugin YoutubeDL will use: %s' % ytdl)

    def prepare_path(self, entry, config):
        # with 'Set' plugin
        path = entry.get('path', config.get('path'))
        if not isinstance(path, str):
            raise plugin.PluginError('Invalid `path` in entry `%s`' % entry['title'])
        try:
            path = os.path.expanduser(entry.render(path))
        except RenderError as e:
            entry.fail('Could not set path. Error during string replacement: %s' % e)
            return
        return path

    def on_task_output(self, task, config):
        for entry in task.accepted:
            path = self.prepare_path(entry, config)
            try:
                outtmpl = os.path.join(path, pathscrub(entry.render(config['template'])))
                logger.debug("Output template: %s" % outtmpl)
            except RenderError as e:
                logger.error('Error setting output file: %s' % e)
                entry.fail('Error setting output file: %s' % e)

            # ytdl options by default
            params = {'quiet': True, 'outtmpl': outtmpl, 'logger': logger, 'noprogress': True}
            # add config to params
            if 'format' in config:
                if config['format']:
                    params.update({'format': config['format']})
            if config.get('other_options'):
                params.update(config['other_options'])
            logger.debug(params)

            if task.options.test:
                logger.info('Would download `{}` in `{}`', entry['title'], path)
            else:
                logger.info('Downloading `{}` in `{}`', entry['title'], path)
                try:
                    with self.ytdl_module.YoutubeDL(params) as ydl:
                        ydl.download([entry['url']])
                except (self.ytdl_module.utils.ExtractorError, self.ytdl_module.utils.DownloadError) as e:
                    entry.fail('Youtube downloader error: %s' % e)
                except Exception as e:
                    entry.fail('Youtube downloader failed. Error message: %s' % e)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginYoutubeDL, 'youtubedl', api_ver=2)
