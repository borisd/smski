from myproject.smski.models import *

import datetime

def Dictionary():
    return "lama box card time bird cat dog cave foot"

def get_sms_last_24h(user):
    return len(SMSMessage.objects.filter(by=user, date__gt=(datetime.datetime.now()-datetime.timedelta(days=1))))

NAMES = ('moshe', 'david', 'haim', 'dani', 'roee', 'avital', 'maayan', 'dafna', 'dganit', 'ravit', 'tzefi', 'ron', 'mishel', 'mark', 'sarit', 'golan', 'dan')
