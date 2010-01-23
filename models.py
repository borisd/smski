from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ''' User profile model '''
    user = models.ForeignKey(User, related_name='profile')
    phone = models.PositiveIntegerField('Phone number')
    display_name = models.CharField('Display name', max_length=10)
    verified = models.BooleanField('Phone verified', default=False)
    friends = models.ManyToManyField(User, related_name='friends')

    def __unicode__(self):
        return u"Profile %s" % self.user

class PhoneVerification(models.Model):
    ''' Model to verify user owns the phone number '''
    user = models.ForeignKey(User)
    phone = models.PositiveIntegerField('Phone number')
    code = models.CharField('Verification code sent', max_length=16)
    attempt = models.IntegerField('Current attempt number')
    date = models.DateTimeField('Time when code was sent')

    def __unicode__(self):
        return u"Verification %s [%s]" % (self.user, self.code)

FRIEND_REQUEST_STATUS = (
    (0, 'Pending'),
    (1, 'Accepted'),
)    

class FriendRequest(models.Model):
    ''' Model for requests to be friends '''
    by = models.ForeignKey(User, related_name='freqby')
    to = models.ForeignKey(User, related_name='freqto')
    date = models.DateTimeField('Time request was sent/accepted')
    status = models.IntegerField(choices=FRIEND_REQUEST_STATUS)

    def __unicode__(self):
        return u'FriendReq %s -> %s' % (self.by, self.to)

SMS_REPLY_TYPES = (
    (0, 'To SMS'),
    (1, 'To email'),
    (2, 'To both'),
)        

class SMSSession(models.Model):
    ''' Wrap a single session (multiple SMS) '''
    date = models.DateTimeField('Time session was created')
    reply_type = models.IntegerField(choices=SMS_REPLY_TYPES)
    user = models.ForeignKey(User, related_name='sms_sessions')

    def __unicode__(self):
        return u'SMSSes %s' % self.user

SMS_STATUSES = (
    (0, 'Sent'),
    (1, 'Received'),
    (2, 'Read'),
    (3, 'Forwarded'),
)        
class SMSMessage(models.Model):
    ''' Singe SMS message '''
    date = models.DateTimeField('Time sms was sent/recieved')
    by = models.ForeignKey(User, related_name='smsby')
    to = models.ForeignKey(User, related_name='smsto')
    session = models.ForeignKey(SMSSession)
    message = models.CharField(max_length=200) # We need to clean this from hacks
    status = models.IntegerField(choices=SMS_STATUSES)
    reply = models.BooleanField(default=False)

    def __unicode__(self):
        return u'SMS %s -> %s' % (self.by, self.to)

class SMSTracker(models.Model):
    date = models.DateTimeField()
    data = models.CharField(max_length=4000)
    parsed = models.BooleanField(default=False)


class DataLog(models.Model):
    msg = models.CharField(max_length=300)
    date = models.DateTimeField()
    user = models.ForeignKey(User, related_name='datalog')
    level = models.PositiveIntegerField(max_length=5, default=0)

    def __unicode__(self):
        return self.msg

