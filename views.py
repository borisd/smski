# Django specific imports
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required #, user_passes_text
from django.contrib.auth.models import User
from django.contrib import auth

# App specific imports
from myproject.smski.models import *
from myproject.smski.forms import *
from myproject.smski.relations import *
from myproject.smski.utils import *
from myproject.smski.log import log


# Utilities
import datetime, re
from itertools import chain

def ready_user(function):
    """
    Decorator for views that checks that:
    - User is logged in
    - User has phone set
    - User has phone verified
    """
    def wrapper(*args, **kwargs):
        user = args[0].user

        if not user.is_authenticated():
            return HttpResponseRedirect("/accounts/login/");

        if not user.get_profile().phone:
            return HttpResponseRedirect("/set_phone/")

        if not user.get_profile().verified:
            return HttpResponseRedirect("/verify_phone/")

        return function(*args, **kwargs)

    return wrapper 

@ready_user
def index(request):
    user = request.user
    
    ajax = request.GET.get('ajax', '')
    if not ajax:
        log.debug('%s: INDEX request' % user)


    def user_html(us, other):
        if us == other:
            return '<span class="user_us">You</span>'
        return '<span class="user">%s</span>' % other

    def info_html(message):
        return '<span class="info">%s</span>' % message

    def build_html(user, by, to, message):
        return "%s%s%s" % (user_html(user, by), info_html(message), user_html(user, to))

    def build_html_reply(user_id):
        return '<a href="/send_message/?to=%d" class="small_btn">reply</a>' % user_id

    def build_html_ac(freq):
        return ''
        html = '''
                <form action="/friend_request/%d/" method="post" style="display:inline">
                <input type="submit" value="%s" name="Action" class="small_btn"/>
                </form>
                ''' % (freq.id, 'Accept' if freq.to == user else 'Cancel')
        return html               

    def freq_info(freq):
        if freq.status == 0:
            message = ' got a friend request from ' 
            extra = build_html_ac(freq)
        else: 
            message = ' accepted friend request from '
            extra = ''

        return { 
                'date': freq.date,
                'html': build_html(user, freq.to, freq.by, message) + extra,
                'message': '',
               }


    def sent_info(sess):
        def build_complex_html(user, msgs):
            result = "%s%s" % (user_html(user, sess.user), info_html(" sent an SMS to "))
            for i in msgs:
                result += "%s, " % user_html(user, i.to)
            result = result[:-2]

            if user != sess.user:
                result += build_html_reply(sess.user.id)
            return result

        msgs = SMSMessage.objects.filter(session=sess).order_by('to')
        if not msgs:
            log.error('%s: Session %d has no messages' % (user, sess.id))
            return None

        return {
                'date': sess.date,
                'html': build_complex_html(user, msgs),
                'message': msgs[0].message,
                }

    def received_info(msg):
        return sent_info(msg.session)


    # Get all the events we show
    freq_list = (FriendRequest.objects.filter(by=user) | FriendRequest.objects.filter(to=user)).distinct()
    received = SMSMessage.objects.filter(to=user)
    sent = SMSSession.objects.filter(user=user)

    total = len(freq_list) + len(sent) + len(received)

    # Handle the new entries script
    if ajax:
        return HttpResponse(total, mimetype='application/javascript')


    freq_data = map(freq_info, freq_list[:50])
    sent_data = map(sent_info, sent[:50])
    received_data = map(received_info, received[:50])

    data = sorted(chain(freq_data, sent_data, received_data), reverse=True)[:50]

    pending = len(FriendRequest.objects.filter(to=user, status=0))

    sent_sms = get_sms_last_24h(user)

    return render_to_response("index.html", {
        'data': data,
        'user': user,
        'pending': pending,
        'sent_sms': sent_sms,
        'total': total,
        })


def new_user(request):
    log.debug('New user request')

    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            uname = data['username']
            upass = data['password']

            user = User.objects.create_user(username=uname, email='', password=upass)
            profile = Profile(user=user, phone=0, display_name=uname, verified=False)
            user.save()
            profile.save()

            user = auth.authenticate(username=uname, password=upass)
            auth.login(request, user)

            log.info('%s: Added new user' % user)

            return HttpResponseRedirect("/set_phone/")
    else:
        form = SignUpForm()

    return render_to_response('new_user.html', { 'form' : form })


@login_required
def set_phone(request):
    log.debug('%s: Set phone request' % request.user)

    user = request.user
    profile = user.get_profile()

    if request.method == 'POST':
        form = SetPhoneForm(user, request.POST)
        if form.is_valid():
            log.info('%s: Successfuly set phone to %s' % (user, profile.phone))
            return HttpResponseRedirect("/verify_phone/")
    else:
        form = SetPhoneForm(user)

    return render_to_response('set_phone.html', { 'form' : form['phone'], 'user' : user, })

@login_required
def verify_phone(request):
    log.debug('%s: Verify phone request' % request.user)

    if not request.user.get_profile().phone:
        return HttpResponseRedirect("/set_phone/")

    user = request.user
    profile = user.get_profile()
    
    if request.method == 'POST':
        form = VerifyPhoneForm(user, request.POST)
        if form.is_valid():
            profile.verified = True;
            profile.save()
            log.info('%s: Verified phone' % user)
            return HttpResponseRedirect("/")
    else:
        form = VerifyPhoneForm(user)

    nice_phone = "%s" % profile.phone
    nice_phone = "0%s-%s" % (nice_phone[0:2], nice_phone[2:])
    return render_to_response('verify_phone.html', { 'form' : form, 'phone' : nice_phone, 'user': user, })

@ready_user
def users(request):
    log.debug('%s: User request' % request.user)

    user = request.user
    def full_info(muser):
        profile = muser.get_profile()
        id = muser.id
        nick = muser.username

        rel, req = relation_and_request(user, muser)
            
        return { 'id':id, 'nick':nick, 'relation':rel, 'reqid': req.id if req else "" }
    
    data = map(full_info, User.objects.filter(profile__verified=True).order_by('username'))

    return render_to_response('user_list.html', { 'data': data, 'REL': REL, 'user': user, })

@ready_user
def friend_request(request, user_id):
    log.debug('%s: Friend request' % request.user)

    muser = get_object_or_404(User, pk=user_id)
    
    if not request.method == 'POST':
        return HttpResponseRedirect("/")

    next_page = request.POST.get("next", "/")

    log.info('%s: Got POST data [%s]' % (request.user, request.POST))

    if muser == request.user:
        return HttpResponseRedirect("/")

    op = request.POST.get("Action", "")

    if op == 'Add':
        log.info("%s: Current relation %d"  % (request.user, relation(muser, request.user)))

        if relation(muser, request.user) != REL.NONE:
            return HttpResponseRedirect("/")
   
        fr = FriendRequest(by=request.user, to=muser, date=datetime.datetime.now(), status=0)
        fr.save()
        log.info("%s: Added friend request %s -> %s" % (request.user, request.user, muser))

    if op == 'Cancel':
        pending = pending_request(request.user, muser)
        if not pending:
            return HttpResponseRedirect("/")

        pending.delete()
        log.info('%s: Removed friend request %s -> %s' % (request.user, request.user, muser))

    if op == 'Accept':
        pending = pending_request(muser, request.user)
        
        if not pending or pending.status:
            return HttpResponseRedirect("/")

        log.info('%s: Accepted friend request %s -> %s' % (request.user, muser, request.user))
        pending.status = 1

        request.user.friends.add(muser.get_profile())
        muser.friends.add(request.user.get_profile())
        request.user.save()
        muser.save()

        pending.save()

    if op == 'Remove':
        rel, req = relation_and_request(muser, request.user)
        if not rel == REL.FRIENDS:
            return HttpResponseRedirect("/")

        if req:
            req.delete()

        muser.friends.remove(request.user.get_profile())
        request.user.friends.remove(muser.get_profile())
        
        log.info('%s: Removed friend link %s -> %s' % (request.user, request.user, muser))


    return HttpResponseRedirect("/user_list/")

@ready_user
def send(request):
    log.debug('%s: Send request' % request.user)

    user = request.user
    profile = user.get_profile()

    send_to = request.GET.get('to', '').split(':')

    if request.method == 'POST':
        form = SendMessageForm(request.POST, user=user)
        if form.is_valid():
            form.action()
            return HttpResponseRedirect("/")
    else:
        form = SendMessageForm(user=user, initial={"recipients":send_to})

    msg = form['message']
    msg_html = msg.as_textarea(attrs={'rows':3, 'cols':30})
    rec = form['recipients']
    rec_html = rec.as_widget()

    total_sms = get_sms_last_24h(user)
    has_friends = len(profile.friends.all())

    return render_to_response('send_message.html', { 
        'msg' : msg,
        'msg_html' : msg_html,
        'rec' : rec,
        'rec_html' : rec_html,
        'total_sms' : total_sms,
        'has_friends' : has_friends, 
        'user': user, })

@ready_user
def logs(request):
    if request.user.username != 'Boris':
        return HttpResponseRedirect("/")

    total = len(DataLog.objects.all())

    ajax = request.GET.get('ajax', '')
    if ajax:
        return HttpResponse(total, mimetype='application/javascript')

    step = 50

    page_str = request.GET.get('page', '1')
    page = int(page_str)


    pages = range(1, (total / step) + 2)
   
    # Paginate
    logs = DataLog.objects.all().order_by('-date')[(page - 1) * step: (page) * step]

    return render_to_response('logs.html', { 
        'logs': logs,
        'pages': pages,
        'total': total,
        'user' : request.user, }) 


