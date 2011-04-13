from __future__ import absolute_import
import logging
from dimagi.utils.gmailloghandler import TLSSMTPHandler

root = logging.getLogger()
root.setLevel(logging.ERROR)
handler = TLSSMTPHandler(
    ('smtp.gmail.com', 587),
    'Uptime Monitor <uptime@dimagi.com>',
    'recipient@domain.com',
    'EWS Ghana Error',
    ('sender@domain.com', 'password')
)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
root.addHandler(handler)
