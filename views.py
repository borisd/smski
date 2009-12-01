# Django specific imports
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required #, user_passes_text
from django.contrib.auth.models import User
from django.contrib import auth

# App specific imports
from myproject.smski.models import Profile
from myproject.smski.forms import SignUpForm, SetPhoneForm, VerifyPhoneFrom

# Utilities
import datetime, re

@login_required
def index(request):
    return render_to_response("index.html", {
        'user' : request.user,
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
    profile = user.get_profile()

    if request.method == 'POST':
        form = SetPhoneForm(user, request.POST)
        if form.is_valid():
            return HttpResponseRedirect("/verify_phone/%s/" % user_id)
    else:
        form = SetPhoneForm(user)

    return render_to_response('generic_form.html', { 'form' : form, })

@login_required
def verify_phone(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile = user.get_profile()

    if request.method == 'POST':
        form = VerifyPhoneFrom(user, request.POST)
        if form.is_valid():
            profile.verified = True;
            profile.save()
            return HttpResponseRedirect("/")
    else:
        form = VerifyPhoneFrom(user)

    return render_to_response('generic_form.html', { 'form' : form, })


