from django import forms
from django.contrib.auth.models import User

from myproject.smski.models import Profile, PhoneVerification
from myproject.smski.utils import Dictionary
from myproject.smski.sms import SMS

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
        print "PV: Old pv found, delete it"
        old_ver[0].delete()

    print "PV: Created new and sending notification"
    pv = PhoneVerification(user=user, phone=phone, code=CreateCode(), attempt=1, date=datetime.datetime.now())
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

    if pv.code != code:
        return 'Incorrect code'

    pv.delete()

    return ''

class SetPhoneForm(forms.Form):
    def __init__(self, user, dict = {}):
        self.user = user
        forms.Form.__init__(self, dict)

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

        profile = self.user.get_profile()

        if phone_numeric != profile.phone:
            profile.profile = phone_numeric
            profile.verified = False
            profile.save()

        error = send_verification(profile.phone, profile.user)
        if error:
            raise forms.ValidationError(error)

        return clean_phone[0:3] + '-' + clean_phone[3:]


class VerifyPhoneFrom(forms.Form):
    def __init__(self, user, dict = {}):
        self.user = user
        forms.Form.__init__(self, dict)

    code = forms.CharField(label='Verification code')

    def clean_code(self):
        code = self.cleaned_data['code']

        error = check_verification(self.user, code)
        if error:
            raise forms.ValidationError(error)

        return code
        
