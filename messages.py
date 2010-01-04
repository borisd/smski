from myproject.smski.models import *
from myproject.smski.log import log
from myproject.smski.utils import NAMES

from django.core.mail import send_mail
from django.conf import settings

from datetime import datetime
import random

def send_mail_message(message, by, to):

    body = message.encode('utf-8')
    dbg = 'Message [%s] => [%s] : [%s]' % (by, to, message)

    if settings.SMS_MODE == 2:
        log.info('SMS: %s' % dbg)
        send_mail('', body, by, [to])
    elif settings.SMS_MODE == 1:
        log.info('EMAIL: %s' % dbg)
        send_mail('', body, by, ['boris@dinkevich.com'])
    else:
        log.info('Info: %s' % dbg)

def send_message(user, message, to_list):
    ses = SMSSession(user=user, date=datetime.now(), reply_type=0)
    ses.save()
    fake_name = random.choice(NAMES)

    for to in to_list:
        log.info("%d:  --- SMS --- [%s] -> [%s] : %s" % (ses.id, user, to, message))
        msg = SMSMessage(date=datetime.now(), by=user, to=to, session=ses, message=message, status=0)
        msg.save()

        if user.username != 'boris' and (to.username == 'admin' or to.username == 'murkin'):
            log.error('%s: Trying to send sms to %s [%s]' % (user, to, message))
            return

        dynamic_addr = '%s <%s%d@do.itlater.com>' % (user, fake_name, ses.id)
        send_mail_message(message, dynamic_addr, "0%s@spikkosms.com" % to.get_profile().phone)

