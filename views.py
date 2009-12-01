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

    def user_link(by):
        return '''<a href="/profile/%s">%s</a>''' % (by.id, by)
    def freq_accept(freq):
        return '''<a href="/friend_request/accept/%s">accept</a>''' % (freq.id)
    def freq_reject(freq):
        return '''<a href="/friend_request/reject/%s">reject</a>''' % (freq.id)
    def freq_cancel(freq):
        return '''<a href="/friend_request/cancel/%s">cancel</a>''' % (freq.id)

    def freq(type, by, to, freq):
        return "Friend request from %s (%s/%s)" % (user_link(freq.by), freq_accept(freq), freq_reject(freq))
    def freq2(by, to, freq):
        return "You rejected %s's friend request" % (user_link(freq.by))
    def freq3(by, to, freq):
        return "You accepted %s's friend request !" % (user_link(freq.by))
    def freq4(by, to, freq):
        return "You sent friend request to %s (%s)" % (user_link(freq.to), freq_cancel(freq))
    def freq5(by, to, freq):
        return "%s accepted your friend request !" % (user_link(freq.to))

    #             ToMe    FromME
    # Pending     freq1   freq4
    # Rejected    freq2   freq4
    # Accepted    freq3   freq5  
    FMap = ((freq1, freq4), (freq2, freq4), (freq4, freq5))

    def full_info(freq):
        return {
                'date': freq.date, 
                'str':FMap[freq.status][freq.to != user](freq.by, freq.to, freq), 
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
        if muser == user:
            relation = 0    # Same user
        elif muser.friends.filter(user=user):
            relation = 1    # Already friend
        elif user.freqto.filter(by=muser):
            relation = 2    # He sent me request
        elif muser.freqto.filter(by=user):
            relation = 3    # I sent him request
        else:
            relation = 4    # Never met.. yet
            
        return { 'id':id, 'nick':nick, 'relation':relation }
    
    data = map(full_info, User.objects.all())

    return render_to_response('user_list.html', { 'data': data, 'user': user, })


