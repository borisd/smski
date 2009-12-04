import sys, email, re, datetime
from BeautifulSoup import BeautifulSoup
from myproject.smski.models import *
from myproject.smski.messages import send_message

def incoming_mail(string):
#    st = SMSTracker(date=datetime.datetime.now(), data=string, parsed=False)
#    st.save()

    msg = email.message_from_string(string)

    data = msg.get_payload()
    if not len(data):
        print 'No payload '
        exit()

    soup = BeautifulSoup(data)
    num = int(re.sub("[^0-9]", '', soup.findAll('font')[1].string)[-9:])
    body = re.sub('=\d.', '', soup.findAll('font')[2].string).strip()

#    st.parsed = True;
#    st.save()

    # Find the session 
    session_id = int(re.search('[0-9]+', (msg['To']).split('@')[0]).group(0), 10)
    if not session_id:
        print "Error getting session id from %s " % msg['To']
        return

    ses = SMSSession.objects.filter(pk=session_id)
    if not len(ses):
        print "Error getting session with id %d" % session_id
        return
    ses = ses[0]

    # Get source user
    print 'Get user for %s' % msg['From']
    by_num = int(re.sub('[^0-9]', '', msg['From'])[-9:])
    if not by_num:
        print "Error parsing orig number %s" % msg['From']
        return

    by_prof = Profile.objects.filter(phone=by_num)
    if not len(by_prof):
        print "Error getting using with num %d" % by_num
        return
        
    by = by_prof[0].user

    print "Got message from %s to %s [%s]" % (by, ses.user, body)

    send_message(by, body, [ses.user])


