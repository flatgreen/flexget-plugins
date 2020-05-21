from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import logging
from flexget import plugin
from flexget.plugin import PluginError, RequestException
from flexget.event import event
import time
import subprocess

log = logging.getLogger('jdownloader')

URL_JD_API_TEST = 'http://127.0.0.1:9666/crossdomain.xml'
URL_JD_API = 'http://127.0.0.1:9666/flashgot'


class PluginJDownloader(object):
    """
    Add url and package name from url and title entries to JDownloader.

    This plugin requires JDownloader2 to download entries.
    It uses the Flashgot interface.
    Prepare the options of JD2 :
        - 'RemoteAPI: Extern Interface Auth' -> ["127.0.0.1"]
        - 'RemoteAPI: Extern Interface' ... will listen on 9666 -> true


    Configuration:

    autostart:  [yes|no] (default: yes) put the link to be immediatly download or not
    runcmd:     path_of_JDownloader if not in service
    to:         destination path, if no set use the default JDownloader2 destination path


    Example 1::
        jdownloader: true

    Example 2::
        jdownloader:
            runcmd: /home/user/.jd/jd.sh

    Example 3::
        jdownloader:
            autostart: 0
            runcmd: c:\Program Files (x86)\JDownloader\JDownloader.exe

    """

    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'autostart': {'type': 'boolean', 'default': True},
                    'runcmd': {'type': 'string', 'default': ''},
                    'to': {'type': 'string', 'default': ''}
                },
                'additionalProperties': False
            }
        ]
    }

    def on_task_output(self, task, config):
        if isinstance(config, bool) and not config:
            return

        config_headers = {'referer': '127.0.0.1'}
        runcmd = config['runcmd']
        autostart = '1' if config['autostart'] else '0'
        dirdl = config['to']

        # JD2 is running ?
        try:
            response = task.requests.get(URL_JD_API_TEST)
        except RequestException as e:
            if runcmd == '':
                raise PluginError('JD not reachable (and no runcmd)', log)
            else:
                log.debug(str(runcmd))
                subprocess.Popen(runcmd)
                # see WAIT_TIME in requests.py
                time.sleep(62)
                try:
                    response = task.requests.get(URL_JD_API_TEST)
                except RequestException as e:
                    raise PluginError('JD not reachable (with runcmd)', log)

        for entry in task.accepted:
            try:
                if task.options.test:
                    log.info('Would add package: %s' % entry['title'])
                else:
                    post_data = {
                        'urls': entry['url'],
                        'autostart': autostart,
                        'package': entry['title'],
                        'dir': dirdl
                    }
                    log.info('url: %s' % entry['url'])
                    response = task.requests.post(URL_JD_API, post_data, headers=config_headers)
                    if response.status_code == 200:
                        log.info('Package added: %s' % entry['title'])
            except Exception as e:
                entry.fail(e)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginJDownloader, 'jdownloader', api_ver=2)
