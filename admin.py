from myproject.smski.models import *
from django.contrib import admin

admin.site.register(Profile)
admin.site.register(PhoneVerification)
admin.site.register(FriendRequest)
admin.site.register(SMSSession)
admin.site.register(SMSMessage)
admin.site.register(SMSTracker)

