# from __future__ import unicode_literals, division, absolute_import
# from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.plugin import PluginWarning
from flexget.utils.requests import Session as RequestSession, TimedLimiter
from requests.exceptions import RequestException

plugin_name = 'sms_free_fr'
logger = logger.bind(name=plugin_name)

SMS_SEND_URL = 'https://smsapi.free-mobile.fr/sendmsg'

requests = RequestSession(max_retries=3)
requests.add_domain_limiter(TimedLimiter('smsapi.free-mobile.fr', '5 seconds'))


class SMSFreeFrNotifier(object):
    """
    Sends SMS notification through smsapi.free-mobile.fr

    Informations:

    https://www.freenews.fr/freenews-edition-nationale-299/free-mobile-170/nouvelle-option-notifications-par-sms-chez-free-mobile-14817

    Example:

    sms_free_fr:
        user: your login (accepted format example: '12345678')
        password: <PASSWORD>


    Full example:

    notify:
      entries:
        via:
          - sms_free_fr:
              user: '{? free_sms.user ?}'
              password: '{? free_sms.password ?}'

    """
    schema = {
        'type': 'object',
        'properties': {
            'user': {"oneOf": [{"type": "string"}, {"type": "integer"}]},
            'password': {'type': 'string'}
        },
        'additionalProperties': False,
        'required': ['user', 'password']
    }

    def notify(self, title, message, config):
        """
        Send an SMS via mobile free.fr notification
        """

        # Build request params
        notification = {'user': config['user'],
                        'pass': config['password'],
                        'msg': message}

        try:
            response = requests.get(SMS_SEND_URL, params=notification)
        except RequestException as e:
            raise PluginWarning(e.args[0])
        else:
            if not response.status_code == 200:
                raise PluginWarning(response.text)


@event('plugin.register')
def register_plugin():
    plugin.register(SMSFreeFrNotifier, plugin_name, api_ver=2, interfaces=['notifiers'])
