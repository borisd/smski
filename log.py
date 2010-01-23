from myproject.smski.models import DataLog

from django.contrib.auth.models import User

import logging
import datetime

log = 0

class db_handler(logging.Handler):
    def __init__(self, user=None):
        logging.Handler.__init__(self)
        if user is None:
            user = User.objects.filter(username='admin')[0]
        self.user = user

    def emit(self, record):
        msg = self.format(record)
        date = datetime.datetime.now()
        entry = DataLog(msg=msg, date=date, user=self.user, level=record.levelno)
        entry.save()
        print msg

def log_init():
    global log

    log = logging.getLogger('main')
    log.addHandler(db_handler())
    log.setLevel(logging.DEBUG)

log_init()

