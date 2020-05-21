from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import os
from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.pathscrub import pathscrub


plugin_name = 'crawljob'
logger = logger.bind(name=plugin_name)


class OutputCrawljob(object):
    """
    This plugin (base make_html) create a .crawljob file for each accepted entry.
    The file name is 'title' and there is 'url' in the text file.
    This file (.crawljob) is for used with JDownloader2

    Requis :
        path: directory for the .crawljob files
        (ex : "C:\\Users\\Julot\\AppData\\Local\\JDownloader 2.0\\folderwatch")

    Example:

    crawljob:
        path: "{? jd2.watch ?}"

    """

    schema = {
        'type': 'object',
        'properties': {
            'path': {'type': 'string'}
        },
        'required': ['path'],
        'additionalProperties': False
    }

    def on_task_output(self, task, config):
        output = os.path.expanduser(config['path'])
        # Output to config directory if absolute path has not been specified
        if not os.path.isabs(output):
            output = os.path.join(task.manager.config_base, output)

        for entry in task.accepted:
            crawljob_file = pathscrub(entry['title'], filename=True)
            real_output = os.path.join(output, crawljob_file) + '.crawljob'
            if task.options.test:
                logger.verbose('Would write output crawljob file to {}', real_output)
                continue
            logger.verbose('Writing output crawljob file to {}', real_output)
            with open(real_output, 'w', encoding='utf-8') as f:
                f.write('text="{0}"\n'.format(entry['url']))
                f.write('deepAnalyseEnabled=true\n')
                f.write('autoStart=true\nautoConfirm=true\n')
                f.write('packageName={0}\n'.format(crawljob_file))


@event('plugin.register')
def register_plugin():
    plugin.register(OutputCrawljob, plugin_name, api_ver=2)
