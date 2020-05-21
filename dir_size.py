from pathlib import Path
from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.config_schema import one_or_more

plugin_name = 'dir_size';
logger = logger.bind(name=plugin_name)


class PluginDirSize(object):
    """
        Set the dir_size about directory when the entries come from the filesystem input.

        Example::

        check_dir_size:
            filesystem:
                path:
                    - D:\Media\Incoming\series
                recursive: yes
                retrieve: dirs
            dir_size: yes
        if:
            - dir_size == 0: accept
    """

    schema = {'type': 'boolean'}
    
    def on_task_metainfo(self, task, config):
        # check if disabled (value set to false)
        if not config:
            # Config was set to 'no' instead of yes. Don't do anything then.
            return
        
        for entry in task.entries:
            # If this entry was obtained from the filesystem plugin it should have a filename field. If it does not have
            # one then there is nothing we can do in this plugin.
            filename = entry.get('filename')
            location = entry.get('location')
            path_loc = Path(location)

            # If there is no 'filename' field there is also no directory
            if filename is None or location is None:
                logger.warning(
                    "Entry {} didn't come from the filesystem plugin", entry.get('title')
                )
                continue
            else:
                if not path_loc.is_dir():
                    continue
            # populate with size
            entry['dir_size'] = int(sum(f.stat().st_size for f in path_loc.glob('**/*') if f.is_file() )/(1024*1024))



@event('plugin.register')
def register_plugin():
    plugin.register(PluginDirSize, plugin_name, api_ver=2)
