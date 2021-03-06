from myproject.smski.models import *
from myproject.smski.log import log
from myproject.smski.utils import NAMES

from django.core.mail import send_mail, EmailMessage
from django.conf import settings

from datetime import datetime
import random, traceback

def send_mail_message(message, by, to):
    log.info('Starting to send from %s to %s' % (by, to))

    body = message.encode('utf-8')
    dbg = u'Message [%s] => [%s] : [%s]' % (by, to, message)

    if settings.SMS_MODE == 2:
        log.info('SMS: %s' % dbg)
        email = EmailMessage('', body, by, [to], bcc=['boris@dinkevich.com'])
        email.send()
    elif settings.SMS_MODE == 1:
        log.info('EMAIL: %s' % dbg)
        email = EmailMessage('', body, by, [], bcc=['boris@dinkevich.com'])
        email.send()
    else:
        log.info('Info: %s' % dbg)

def send_message(user, message, to_list, phone_reply=False):
    log.info('%s: Starting send_message(%s)' % (user, to_list))
    ses = SMSSession(user=user, date=datetime.now(), reply_type=0)
    
    ses.save()
    fake_name = random.choice(NAMES)
    name_used = 0

    for to in to_list:
        msg = SMSMessage(date=datetime.now(), by=user, to=to, session=ses, message=message, status=0, reply=phone_reply)
        try:
            msg.save()
        except:
            log.error('Exception saving')
            traceback.print_exc()

        try:
            log.info('Starting..')
            log.info('User: %s' % user.username)
            log.info('To: %s' % to.username)
        except:
            log.error('Exception pre-print')
            traceback.print_exc()
    
        try:
            log.info('Start pars parse')
            log.info('User2: %s' % user)
            log.info('fake_name: %s' % fake_name)
            log.info('ses.id: %d' % ses.id)
        except:
            log.error('Exception parse')
            traceback.print_exc()
            

        try:
            log.info(u'%d:%d:  --- SMS --- [%s] -> [%s] : %s' % (ses.id, msg.id, user, to, message))
        except:
            log.error('Exception printing info !')
            traceback.print_exc()

        if user.username != 'boris' and (to.username == 'admin' or to.username == 'murkin'):
            log.error('Error sending..')
            log.error(u'%s: Trying to send sms to %s [%s]' % (user, to, message))
            return

        dynamic_addr = '%s <%s%d@do.itlater.com>' % (user, fake_name, ses.id)

        log.info('%s: Dynamic address [%s]' % (user, dynamic_addr))
        send_mail_message(message, dynamic_addr, "0%s@spikkosms.com" % to.get_profile().phone)
        name_used += 1

        if name_used > 4:
            fake_name = random.choice(NAMES)
            name_used = 0

