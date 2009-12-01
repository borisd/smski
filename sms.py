from django.contrib.auth.models import User

class SMS:
    def __init__(self, user, message):
        print "--- SMS --- : to: %s message: %s" % (user, message)

