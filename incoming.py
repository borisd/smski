import sys, email, re, datetime, quopri

from BeautifulSoup import BeautifulSoup

from myproject.smski.models import *
from myproject.smski.messages import send_message
from myproject.smski.log import log

def parse_incoming_mail(string):
    log.info('Parsing new email')
#    st = SMSTracker(date=datetime.datetime.now(), data=string, parsed=False)
#    st.save()

    msg = email.message_from_string(string)

    data = msg.get_payload()
    if not len(data):
        log.error('No payload !')
        exit()

    try:
        soup = BeautifulSoup(data)
    except:
        log.error('Error loading Soup')

    try:
        str = soup.findAll('font')[1].string)[-9:]
    except:
        log.error('Error getting number')

    try:
        num = int(re.sub("[^0-9]", '', str))
    except:
        log.error('Error getting num for [%s]' % str)

    try:
        str = soup.findAll('font')[2].string
    except:
        log.error('Error getting body')

    try:
        body = re.sub('=\d.', '', str).strip()
    except:
        log.error('Error getting body [%s]' % str)


#    st.parsed = True;
#    st.save()

    # Find the session 
    str = re.search('[0-9]+', (msg['To']).split('@')[0]).group(0)
    try:
        session_id = int(str, 10)
    except:
        log.error('Error getting session id [%s]' % str)

    if not session_id:
        log.error("Error getting session id from %s " % msg['To'])
        return

    ses = SMSSession.objects.filter(pk=session_id)
    if not len(ses):
        log.error("Error getting session with id %d" % session_id)
        return
    ses = ses[0]

    # Get source user
    log.info('Get user for %s' % msg['From'])
    by_num = int(re.sub('[^0-9]', '', msg['From'])[-9:])
    if not by_num:
        log.error("Error parsing orig number %s" % msg['From'])
        return

    by_prof = Profile.objects.filter(phone=by_num)
    if not len(by_prof):
        log.error("Error getting using with num %d" % by_num)
        return
        
    by = by_prof[0].user

    log.info("Got message from %s to %s [%s]" % (by, ses.user, body))

    body_w1255 = quopri.decodestring(body)
    decoded_body = body_w1255.decode('windows-1255').strip()

    send_message(by, decoded_body, [ses.user])

def incoming_mail(string):
    try:
        parse_incoming_mail(string)
    except:
        log.error("Exception parsing email")


