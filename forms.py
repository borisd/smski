from django import forms
from django.contrib.auth.models import User, check_password
from django.utils.safestring import mark_safe

from myproject.smski.models import Profile, PhoneVerification
from myproject.smski.utils import *
from myproject.smski.messages import send_message
from myproject.smski.log import log

import re, random, datetime

def check_phone_validity(dirty_phone, user):
    ''' Check to see if a string represents a valid phone number '''

    clean_phone = re.sub('[- .\t]', '', dirty_phone)
    if re.sub('[0-9]', '', clean_phone) != '':
        log.info('%s: Invalid chars in phone: [%s]' % (user, clean_phone))
        raise forms.ValidationError("Please use only numbers and '-' in phone number")

    if clean_phone[0] != '0' or clean_phone[1] != '5':
        log.info('%s: Unsupported phone format [%s]' % (user, clean_phone))
        raise forms.ValidationError("Only '05x-xxxxxxx' phones are supported")

    if len(clean_phone) != 10:
        log.info('%s: Incorrect number of digits in phone [%s]' % (user, clean_phone))
        raise forms.ValidationError("Number should have 10 digits, you entered only %d" % len(clean_phone))

    return int(clean_phone, 10)

def CreateCode(user):
    random.seed()
    opts = Dictionary().split(' ')
    code = "%s%d" % (opts[random.randint(0, len(opts)-1)], random.randint(11,99))
    log.info('%s: Generated random code for verification [%s]' % (user, code))
    return code

class ResetPWForm(forms.Form):
    username = forms.CharField(max_length=30, min_length=3, label='Username')
    phone = forms.CharField(label='Cell phone number')

    def clean_phone(self):
        phone = check_phone_validity(self.cleaned_data['phone'], self.cleaned_data['username'])
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            log.error('Trying to reset password for unknown user [%s]' % self.cleaned_data['username'])
            raise forms.ValidationError("Unknown User and Phone combination")

        if user.get_profile().phone != phone:
            log.error('Not matching user/phone User: %s Real Phone: %d Attempted %d' % 
                    (self.cleaned_data['username'], user.get_profile().phone, phone))
            raise forms.ValidationError("Unknown User and Phone combination")

        return phone

    def execute(self):
        user = User.objects.get(username__iexact=self.cleaned_data['username'])
        new_pass = CreateCode(user)

        log.info('%s: Password has been reset to %s' % (user, new_pass))

        user.set_password(new_pass)
        user.save()
        send_message(User.objects.filter(username='admin')[0], 'SMSKI: Your password has been reset to: %s' % new_pass, [user])

class SignUpForm(forms.Form):
    username = forms.CharField(max_length=30, min_length=3, label='Username')
    password = forms.CharField(widget=forms.PasswordInput, max_length=100, min_length=3, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=100, min_length=3, label='Retype Password')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username):
            log.info('User tried to register with %s - already take' % username)
            raise forms.ValidationError('Username already taken')
        return username

    def clean_password2(self):
        pw  = self.cleaned_data.get('password', '')
        pw2 = self.cleaned_data.get('password2', '')

        if pw != pw2:
            raise forms.ValidationError('Passwords do not match')

        return pw

def send_verification(phone, user):
    old_ver = PhoneVerification.objects.filter(user=user)

    # TODO: Handle flooding of verifications
    if old_ver:
        time_diff = (datetime.datetime.now() - old_ver[0].date).seconds
        if time_diff < 60 * 5:
            log.info('%s: User impatient, request ver only after %d seconds' % (user, time_diff))
            return "Please give the sms %d more minutes to get there" % (5 - time_diff / 60)

        log.info('%s: Found old PhoneVerification, delete for now' % (user))
        old_ver[0].delete()

    log.info("%s: Created new PhoneVerification and sending notification" % (user))
    pv = PhoneVerification(user=user, phone=phone, code=CreateCode(user).lower(), attempt=1, date=datetime.datetime.now())
    pv.save()
    send_message(User.objects.filter(username='admin')[0], 'Your code for SMSKI is: %s' % pv.code, [user])

    return ''

def check_verification(user, code):
    pv_list = PhoneVerification.objects.filter(user=user)
    if not pv_list:
        log.warning('%s Checking verification when once was not yet sent' % (user))
        return 'No verification code was sent yet'

    pv = pv_list[0]

    if pv.phone != user.get_profile().phone:
        log.warning('%s: Entered verification for different phone %s != %s' % (user, pv.phone, user.get_profile().phone))
        return 'Verification code for a phone different then what user has'

    if pv.code != code.lower():
        log.warning('%s: Incorrect Verification code' % (user))
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

        phone_numeric = check_phone_validity(dirty_phone, self.user)

        # Prevent two users using the same phone
        query = Profile.objects.filter(phone=phone_numeric)
        if query and query[0].verified:
            log.warning('%s: tried to enter phone %s which belongs to %s' % (self.user, clean_phone, query[0].user))
            raise forms.ValidationError("Number already registered by %s" % query[0].user)

        profile = self.user.get_profile()

        # Update phone
        if phone_numeric != profile.phone:
            log.info('%s: changed phone %s -> %s' % (self.user, profile.phone, phone_numeric))
            profile.phone = phone_numeric
            profile.verified = False
            profile.save()

        # Start verification process
        error = send_verification(profile.phone, profile.user)
        if error:
            log.warning('%s: Phone verification failed [%s]' % (self.user, error))
            raise forms.ValidationError(error)

        return phone_numeric


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
            log.warning("%s: code verification failed [%s]" % (self.user, error))
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
            log.info('%s: tried to send to %d people' % (self.user, len(rcp)))
            raise forms.ValidationError('Cannot send to more then 10 people')

        if len(rcp) + get_sms_last_24h(self.user) > 30:
            log.warning('%s: tried to send to more then 30 people' % self.user)
            raise forms.ValidationError('Cannot send more then 30 SMS a day')

        for i in rcp:
            last = SMSMessage.objects.filter(by=self.user, to=i, date__gt=(datetime.datetime.now()-datetime.timedelta(minutes=1)))
            if last:
                log.warning('%s: trying to send too fast' % self.user)
                raise forms.ValidationError('You can send again to %s in %s seconds' % (i, 60 - (datetime.datetime.now() - last[0].date).seconds))

        return rcp

    def action(self):
        send_message(self.user, self.cleaned_data['message'], self.cleaned_data['recipients'])
