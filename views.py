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

# Utilities
import datetime, re
from itertools import chain

@login_required
def index(request):
    user = request.user

    user_link   = lambda by:   '''<a href="/profile/%s">%s</a>''' % (by.id, by)
    freq_accept = lambda freq: '''<a href="/friend_request/accept/%s">accept</a>''' % (freq.id)
    freq_reject = lambda freq: '''<a href="/friend_request/reject/%s">reject</a>''' % (freq.id)
    freq_cancel = lambda freq: '''<a href="/friend_request/cancel/%s">cancel</a>''' % (freq.id)

    freq1 = lambda freq: ("Friend request from %s (%s/%s)" % (user_link(freq.by), freq_accept(freq), freq_reject(freq)))
    freq2 = lambda freq: ("You accepted %s's friend request !" % (user_link(freq.by)))
    freq3 = lambda freq: ("You sent friend request to %s (%s)" % (user_link(freq.to), freq_cancel(freq)))
    freq4 = lambda freq: ("%s accepted your friend request !" % (user_link(freq.to)))

    #             ToMe    FromME
    # Pending     freq1   freq3
    # Accepted    freq2   freq4  
    FMap = ((freq1, freq3), (freq2, freq4))

    def freq_info(freq):
        return {
                'date': freq.date, 
                'str':FMap[freq.status][freq.to != user](freq),
                }
    def msg_info(msg):
        return { 
                'date': msg.date,
                'str': "SMS from %s to %s: %s" % (msg.by, msg.to, msg.message)
               }

    freq_list = (FriendRequest.objects.filter(by=user) | FriendRequest.objects.filter(to=user)).distinct().order_by('date')[:100]
    freq_data = map(freq_info, freq_list)

    msg_list = (SMSMessage.objects.filter(by=user) | SMSMessage.objects.filter(to=user)).distinct().order_by('date')[:100]
    msg_data = map(msg_info, msg_list)

    data = sorted(chain(freq_data, msg_data))


    return render_to_response("index.html", {
        'data': data,
        'user': request.user,
        })


def new_user(request):
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
            return HttpResponseRedirect("/set_phone/%d/" % user.id)
    else:
        form = SignUpForm()

    return render_to_response('new_user.html', { 'form' : form })


@login_required
def set_phone(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user != request.user:
        return HttpResponseRedirect("/")
    profile = user.get_profile()

    if request.method == 'POST':
        form = SetPhoneForm(user, request.POST)
        if form.is_valid():
            return HttpResponseRedirect("/verify_phone/%s/" % user_id)
    else:
        form = SetPhoneForm(user)

    return render_to_response('set_phone.html', { 'form' : form['phone'], 'user' : user, })

@login_required
def verify_phone(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user != request.user:
        return HttpResponseRedirect("/")

    profile = user.get_profile()

    if request.method == 'POST':
        form = VerifyPhoneForm(user, request.POST)
        if form.is_valid():
            profile.verified = True;
            profile.save()
            return HttpResponseRedirect("/")
    else:
        form = VerifyPhoneForm(user)

    return render_to_response('verify_phone.html', { 'form' : form, 'phone' : profile.phone, 'user': user, })

@login_required
def users(request):
    
    user = request.user

    def full_info(muser):
        profile = muser.get_profile()
        id = muser.id
        nick = muser.username

        rel, req = relation_and_request(user, muser)
            
        return { 'id':id, 'nick':nick, 'relation':rel, 'reqid': req.id if req else "" }
    
    data = map(full_info, User.objects.all().order_by('username'))

    return render_to_response('user_list.html', { 'data': data, 'user': user, })

@login_required
def friend_request(request, user_id):
    muser = get_object_or_404(User, pk=user_id)

    if not request.method == 'POST':
        return HttpResponseRedirect("/")

    print request.POST

    if muser == request.user:
        return HttpResponseRedirect("/")

    op = request.POST.get("Action", "")

    if op == 'Add':
        if relation(muser, request.user) != REL_NONE:
            return HttpResponseRedirect("/")
   
        fr = FriendRequest(by=request.user, to=muser, date=datetime.datetime.now(), status=0)
        fr.save()
        print "Added"

    if op == 'Cancel':
        pending = pending_request(request.user, muser)
        if not pending:
            return HttpResponseRedirect("/")

        pending.delete()
        print "Removed"

    if op == 'Accept':
        pending = pending_request(muser, request.user)
        
        if not pending or pending.status:
            return HttpResponseRedirect("/")

        print "Changing to %s" % op
        pending.status = 1
        request.user.friends.add(muser.get_profile())
        muser.friends.add(request.user.get_profile())
        request.user.save()
        muser.save()
        pending.save()

    if op == 'Remove':
        rel, req = relation_and_request(muser, request.user)
        if not rel == REL_FRIENDS:
            return HttpResponseRedirect("/")

        if req:
            req.delete()

        muser.friends.remove(request.user.get_profile())
        request.user.friends.remove(muser.get_profile())



    return HttpResponseRedirect("/")

@login_required
def send(request):
    user = request.user
    profile = user.get_profile()

    if request.method == 'POST':
        form = SendMessageForm(request.POST, user=user)
        if form.is_valid():
            form.action()
            return HttpResponseRedirect("/")
    else:
        form = SendMessageForm(user=user)

    msg = form['message']
    msg_html = msg.as_textarea(attrs={'rows':3, 'cols':30})
    rec = form['recipients']
    rec_html = rec.as_widget()

    return render_to_response('send_message.html', { 
        'msg' : msg,
        'msg_html' : msg_html,
        'rec' : rec,
        'rec_html' : rec_html,
        'user': user, })

