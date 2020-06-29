from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin
import logging

from flexget import plugin
from flexget.event import event
from flexget.utils.template import RenderError
from flexget.utils.pathscrub import pathscrub
import os
import glob


log = logging.getLogger('youtubedl')

# Inspiration :
# https://github.com/z00nx/flexget-plugins/blob/master/youtubedl.py
# see discussion : https://github.com/Flexget/Flexget/pull/65

# TODO:
# - add descriptions https://flexget.readthedocs.io/en/latest/develop/schemas.html#title-and-description
# - if path doesn't exist check fail (and execute)
# FIXME/REVIEW/TEST OR NOT: youtube-dl fails when falling back to generic download method -> log.error


class PluginYoutubeDL(object):
    """
    Download videos using YoutubeDL

    This plugin requires the 'youtube-dl' Python module.
    To install the Python module run:
    'pip install youtube-dl'

    Web site : https://github.com/rg3/youtube-dl

    Configuration:

    username:       Login with this account ID (option)
    password:       Account password (option)
    videopassword:  Video password (vimeo, smotri, youku)
    format:         Video format code (default: best)
    template:       Output filename template (default: '%(title)s-%(id)s.%(ext)s')
    path:           Destination path (can be use with 'Set' plugin)
    json:           (true/false) like youtube-dl option 'writeinfojson' without '.info' in filename
    other_options:  all parameters youtube-dl can accept
                    (see : https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py)

    'template' and 'path' support Jinja2 templating on the input entry

    Examples::

    youtubedl:
        format: best
        template: {{ title }}.%(ext)s
        path: ~/downloads/

    youtubedl:
        path: 'E:\--DL--\'
        other_options:
            writeinfojson: true
    """

    schema = {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'format': {'type': 'string', 'default': 'best'},
            'template': {'type': 'string', 'default': '%(title)s-%(id)s.%(ext)s'},
            'videopassword': {'type': 'string'},
            'path': {'type': 'string', 'format': 'path'},
            'json': {'type': 'boolean'},
            'other_options': {'type': 'object'}
        },
        'additionalProperties': False
    }

    def on_task_start(self, task, config):
        try:
            import youtube_dl  # NOQA
        except ImportError as e:
            log.debug('Error importing YoutubeDL: %s' % e)
            raise plugin.DependencyError('youtubedl', 'youtubedl',
                                         'youtubedl module required. ImportError: %s' % e)

    def prepare_path(self, entry, config):
        path = entry.get('path', config.get('path'))
        if not isinstance(path, str):
            raise plugin.PluginError('Invalid `path` in entry `%s`' % entry['title'])
        try:
            path = entry.render(path)
        except RenderError as e:
            entry.fail('Could not set path. Error during string replacement: %s' % e)
            return
        try:
            path = os.path.expanduser(entry.render(path))
        except RenderError as e:
            entry.fail('Could not set path. Error during string replacement: %s' % e)
            return
        return path

    def on_task_output(self, task, config):
        import youtube_dl.YoutubeDL
        from youtube_dl.utils import ExtractorError

        for entry in task.accepted:
            path = self.prepare_path(entry, config)

            try:
                # combine to full path + filename
                outtmpl = os.path.join(path, pathscrub(entry.render(config['template'])))
                log.debug("Output file: %s" % outtmpl)
            except RenderError as e:
                log.error('Error setting output file: %s' % e)
                entry.fail('Error setting output file: %s' % e)

            # options by default
            params = {'quiet': True, 'outtmpl': outtmpl, 'logger': log, 'noprogress': True}
            # with config
            if 'username' in config and 'password' in config:
                params.update({'username': config['username'], 'password': config['password']})
            elif 'username' in config or 'password' in config:
                log.error('Both username and password is required')
            if 'videopassword' in config:
                params.update({'videopassword': config['videopassword']})
            if 'format' in config:
                params.update({'format': config['format']})
            if 'json' in config:
                params.update({'writeinfojson': config['json']})
            if config.get('other_options'):
                params.update(config['other_options'])

            if task.options.test:
                log.info('Would download `%s` in `%s`', entry['title'], path)
                log.info('options `%s`', params)
            else:
                log.info('Downloading `%s` in `%s`', entry['title'], path)
                try:
                    with youtube_dl.YoutubeDL(params) as ydl:
                        ydl.download([entry['url']])
                except ExtractorError as e:
                    entry.fail('Youtube-DL was unable to download the video. Error message %s' % e.message)
                except Exception as e:
                    entry.fail('Youtube-DL failed. Error message %s' % e.message)

                if config.get('json'):
                    for json_file in glob.iglob(path + "/*.info.json"):
                        new_json_file = json_file.replace('.info', '')
                        os.rename(json_file, new_json_file)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginYoutubeDL, 'youtubedl', api_ver=2)
