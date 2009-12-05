from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from myproject.smski.models import Profile, PhoneVerification
from myproject.smski.utils import *
from myproject.smski.sms import SMS
from myproject.smski.messages import send_message

import re, random, datetime

class SignUpForm(forms.Form):
    username = forms.CharField(max_length=30, min_length=3, label='Username')
    password = forms.CharField(widget=forms.PasswordInput, max_length=100, min_length=3, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=100, min_length=3, label='Retype Password')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError('Username already taken')
        return username

    def clean_password2(self):
        pw  = self.cleaned_data.get('password', '')
        pw2 = self.cleaned_data.get('password2', '')

        if pw != pw2:
            raise forms.ValidationError('Passwords do not match')

        return pw

def send_verification(phone, user):
    def CreateCode():
        random.seed()
        opts = Dictionary().split(' ')
        code = "%s%d" % (opts[random.randint(0, len(opts)-1)], random.randint(11,99))
        print "Generated random code [%s]" % code
        return code

    old_ver = PhoneVerification.objects.filter(user=user)

    # TODO: Handle flooding of verifications
    if old_ver:
        time_diff = (datetime.datetime.now() - old_ver[0].date).seconds
        if time_diff < 60 * 5:
            return "Please give the sms %d more minutes to get there" % (5 - time_diff / 60)

        print "PV: Old pv found, delete it"
        old_ver[0].delete()

    print "PV: Created new and sending notification"
    pv = PhoneVerification(user=user, phone=phone, code=CreateCode().lower(), attempt=1, date=datetime.datetime.now())
    pv.save()
    SMS(user, "Your verification code is: %s" % pv.code)

    return ''

def check_verification(user, code):
    pv_list = PhoneVerification.objects.filter(user=user)
    if not pv_list:
        return 'No verification code was sent yet'

    pv = pv_list[0]

    if pv.phone != user.get_profile().phone:
        return 'Verification code for a phone different then what user has'

    if pv.code != code.lower():
        return 'Incorrect code'

    pv.delete()

    return ''

class SetPhoneForm(forms.Form):
    def __init__(self, user, dict = {}):
        if dict:
            forms.Form.__init__(self, dict)
        else:
            forms.Form.__init__(self)
        self.user = user

    phone = forms.CharField(label='Cell phone number')

    def clean_phone(self):
        dirty_phone = self.cleaned_data['phone']
        clean_phone = re.sub('[- .\t]', '', dirty_phone)
        if re.sub('[0-9]', '', clean_phone) != '':
            raise forms.ValidationError("Please use only numbers and '-' in phone number")

        if clean_phone[0] != '0' or clean_phone[1] != '5':
            raise forms.ValidationError("Only '05x-xxxxxxx' phones are supported")

        if len(clean_phone) != 10:
            raise forms.ValidationError("Number should have 10 digits, you entered only %d" % len(clean_phone))

        phone_numeric = int(clean_phone, 10)

        # Prevent two users using the same phone
        query = Profile.objects.filter(phone=phone_numeric)
        if query and query[0].verified:
            raise forms.ValidationError("Number already registered by %s" % query[0].user)

        profile = self.user.get_profile()

        # Update phone
        if phone_numeric != profile.phone:
            profile.phone = phone_numeric
            profile.verified = False
            profile.save()

        # Start verification process
        error = send_verification(profile.phone, profile.user)
        if error:
            raise forms.ValidationError(error)

        return clean_phone[0:3] + '-' + clean_phone[3:]


class VerifyPhoneForm(forms.Form):
    def __init__(self, user, dict = {}):
        self.user = user
        if dict:
            forms.Form.__init__(self, dict)
        else:
            forms.Form.__init__(self)

    code = forms.CharField(label='')

    def clean_code(self):
        code = self.cleaned_data['code']

        error = check_verification(self.user, code)
        if error:
            raise forms.ValidationError(error)

        send_message(User.objects.filter(pk=1)[0], "Welcome aboard ! Add some friends and start SMSing !", [self.user])
        return code

class CheckboxSelectMultipleP(forms.CheckboxSelectMultiple):
    def render(self, *args, **kwargs):
        output = super(CheckboxSelectMultipleP, self).render(*args, **kwargs)
        return mark_safe(output.replace(u'<li>', u'<li class="send_msg user">').replace(u'<ul>', u'<ul class="send_msg">'))

class SendMessageForm(forms.Form):
    message = forms.CharField(max_length=50, label='Message to send')
    recipients = forms.ModelMultipleChoiceField(queryset='', widget=CheckboxSelectMultipleP())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        forms.Form.__init__(self, *args, **kwargs)
        self.fields['recipients'].queryset = self.user.get_profile().friends.all()


    def clean_recipients(self):
        rcp = self.cleaned_data['recipients']
        if len(rcp) > 10:
            raise forms.ValidationError('Cannot send to more then 10 people')

        if len(rcp) + get_sms_last_24h(self.user) > 30:
            raise forms.ValidationError('Cannot send more then 30 SMS a day')

        return rcp

    def action(self):
        send_message(self.user, self.cleaned_data['message'], self.cleaned_data['recipients'])
