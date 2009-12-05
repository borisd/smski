from myproject.smski.models import *
from django.core.mail import send_mail

from datetime import datetime

def send_mail_message(message, by, to):
        print "Message [%s] => [%s] : [%s]" % (by, to, message)
        send_mail('', message, by, ['boris@dinkevich.com'])
#        send_mail('', message, by, [to])

def send_message(user, message, to_list):
    ses = SMSSession(user=user, date=datetime.now(), reply_type=0)
    ses.save()

    for to in to_list:
        print "%d:  --- SMS --- [%s] -> [%s] : %s" % (ses.id, user, to, message)
        msg = SMSMessage(date=datetime.now(), by=user, to=to, session=ses, message=message, status=0)
        msg.save()

        dynamic_addr = '%s <moshe%d@do.itlater.com>' % (user, ses.id)
        send_mail_message(message, dynamic_addr, "0%s@spikkosms.com" % to.get_profile().phone)

