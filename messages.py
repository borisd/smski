from myproject.smski.models import *
from django.core.mail import send_mail
from django.conf import settings

from datetime import datetime
import logging as log

def send_mail_message(message, by, to):
    dbg = 'Message [%s] => [%s] : [%s]' % (by, to, message)

    if settings.SMS_MODE == 2:
        log.info('SMS: %s' % dbg)
        send_mail('', message, by, [to])
    elif settings.SMS_MODE == 1:
        log.info('EMAIL: %s' % dbg)
        send_mail('', message, by, ['boris@dinkevich.com'])
    else:
        log.info('Info: %s' % dbg)


def send_message(user, message, to_list):
    ses = SMSSession(user=user, date=datetime.now(), reply_type=0)
    ses.save()

    for to in to_list:
        log.info("%d:  --- SMS --- [%s] -> [%s] : %s" % (ses.id, user, to, message))
        msg = SMSMessage(date=datetime.now(), by=user, to=to, session=ses, message=message, status=0)
        msg.save()

        if to.username == 'admin' or to.username == 'murkin':
            log.error('%s: Trying to send sms to %s [%s]' % (user, to, message))
            return

        dynamic_addr = '%s <moshe%d@do.itlater.com>' % (user, ses.id)
        send_mail_message(message, dynamic_addr, "0%s@spikkosms.com" % to.get_profile().phone)

