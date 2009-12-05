#!/usr/local/bin/python2.5
import settings
from django.core.management import setup_environ

setup_environ(settings)

f = open('/home/murkin/webapps/django/myproject/log.txt', 'a')
f.write('Got email\n')
f.close()

msg = sys.stdin.read()

dump = open('/home/murkin/webapps/django/myproject/dump.txt', 'w')
dump.write(msg)
dump.close()

from myproject.smski.incoming import incoming_mail

incoming_mail(msg)


