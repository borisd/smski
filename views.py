# Django specific imports
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required #, user_passes_text
from django.contrib.auth.models import User
from django.contrib import auth

# App specific imports
from myproject.smski.models import Profile, FriendRequest
from myproject.smski.forms import SignUpForm, SetPhoneForm, VerifyPhoneForm

# Utilities
import datetime, re

@login_required
def index(request):
    user = request.user

    user_link   = lambda by:   '''<a href="/profile/%s">%s</a>''' % (by.id, by)
    freq_accept = lambda freq: '''<a href="/friend_request/accept/%s">accept</a>''' % (freq.id)
    freq_reject = lambda freq: '''<a href="/friend_request/reject/%s">reject</a>''' % (freq.id)
    freq_cancel = lambda freq: '''<a href="/friend_request/cancel/%s">cancel</a>''' % (freq.id)

    freq1 = lambda freq: ("Friend request from %s (%s/%s)" % (user_link(freq.by), freq_accept(freq), freq_reject(freq)))
    freq2 = lambda freq: ("You rejected %s's friend request" % (user_link(freq.by)))
    freq3 = lambda freq: ("You accepted %s's friend request !" % (user_link(freq.by)))
    freq4 = lambda freq: ("You sent friend request to %s (%s)" % (user_link(freq.to), freq_cancel(freq)))
    freq5 = lambda freq: ("%s accepted your friend request !" % (user_link(freq.to)))

    #             ToMe    FromME
    # Pending     freq1   freq4
    # Rejected    freq2   freq4
    # Accepted    freq3   freq5  
    FMap = ((freq1, freq4), (freq2, freq4), (freq4, freq5))

    def full_info(freq):
        return {
                'date': freq.date, 
                'str':FMap[freq.status][freq.to != user](freq),
                }

    list = FriendRequest.objects.filter(by=user) | FriendRequest.objects.filter(to=user)
    list.distinct()
    list.order_by('-date')

    data = map(full_info, list)

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
        req = []
        if muser == user:
            relation = 0    # Same user
        elif muser.friends.filter(user=user):
            relation = 1    # Already friend
        elif user.freqto.filter(by=muser):
            req = user.freqto.filter(by=muser)[0].id
            relation = 2    # He sent me request
        elif muser.freqto.filter(by=user):
            req = muser.freqto.filter(by=user)[0].id
            relation = 3    # I sent him request
        else:
            relation = 4    # Never met.. yet
            
        return { 'id':id, 'nick':nick, 'relation':relation, 'reqid':req }
    
    data = map(full_info, User.objects.all())

    return render_to_response('user_list.html', { 'data': data, 'user': user, })

def friend_request(request, action, request_id):
    pass

