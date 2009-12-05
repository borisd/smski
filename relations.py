from myproject.smski.models import Profile, FriendRequest

import logging as log

def pending_request(user_a, user_b):
    reqs = user_b.freqto.filter(by=user_a)
    if reqs:
        return reqs[0]
    return False

def friends(user_a, user_b):
    return user_a.friends.filter(user=user_b)

class REL:
    NONE = 0
    FRIENDS = 1
    A2B = 2
    B2A = 3
    SAME = 4


def relation_and_request_d(user_a, user_b):
    ''' Map different user relations 
    0 - No relation
    1 - Friends
    2 - User A sent B a friend request
    3 - User B sent A a friend request
    4 - Same user
    '''

    req = ""

    if user_a == user_b:
        return REL.SAME, req

    if friends(user_a, user_b):
        return REL.FRIENDS, req

    req = pending_request(user_a, user_b)
    if req and req.status == 0:
        return REL.A2B, req

    req = pending_request(user_b, user_a)
    if req and req.status == 0:
        return REL.B2A, req

    return REL.NONE, req

def relation_and_request(user_a, user_b):
    a,b = relation_and_request_d(user_a, user_b)
    log.info('Relation %s : %s is %d' % (user_a, user_b, a))
    return a,b

def relation(user_a, user_b):
    id, req = relation_and_request(user_a, user_b)
    return id

