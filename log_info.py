from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.config_schema import one_or_more

plugin_name = 'log_info';
logger = logger.bind(name=plugin_name)

# version pour flexget 3.


class PluginLogInfo(object):
    """
        Write a message (with jinja2 replacement)
        to the system logging with level=INFO for accepted entries ::

            log_info: <message>


        Example::

            log_info: a message for the log file !

        Example::

            log_info: 'download: {{ url }}'
    """

    schema = one_or_more({'type': 'string'})

    def on_task_output(self, task, config):
        if not isinstance(config, list):
            config = [config]

        test = '--test ' if task.options.test else ''
        for entry in task.accepted:
            for mes in config:
                logger.info(test + entry.render(mes))


@event('plugin.register')
def register_plugin():
    plugin.register(PluginLogInfo, plugin_name, api_ver=2)
