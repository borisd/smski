from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ''' User profile model '''
    user = models.ForeignKey(User, related_name='profile')
    phone = models.PositiveIntegerField('Phone number')
    display_name = models.CharField('Display name', max_length=10)
    verified = models.BooleanField('Phone verified', default=False)
    friends = models.ManyToManyField(User, related_name='friends')


class PhoneVerification(models.Model):
    ''' Model to verify user owns the phone number '''
    user = models.ForeignKey(User)
    phone = models.PositiveIntegerField('Phone number')
    code = models.CharField('Verification code sent', max_length=16)
    attempt = models.IntegerField('Current attempt number')
    date = models.DateTimeField('Time when code was sent')

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

