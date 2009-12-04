from myproject.smski.models import Profile, FriendRequest

def pending_request(user_a, user_b):
    reqs = user_b.freqto.filter(by=user_a)
    if reqs:
        return reqs[0]
    return False

def friends(user_a, user_b):
    return user_a.friends.filter(user=user_b)

REL_SAME = 0
REL_FRIENDS = 1
REL_NONE = 2
REL_A2B = 3
REL_B2A = 4


def relation_and_request(user_a, user_b):
    ''' Map different user relations 
    0 - No relation
    1 - Friends
    2 - User A sent B a friend request
    3 - User B sent A a friend request
    4 - Same user
    '''

    req = ""

    if user_a == user_b:
        return REL_SAME, req

    if friends(user_a, user_b):
        return REL_FRIENDS, req

    req = pending_request(user_a, user_b)
    if req and req.status == 0:
        return REL_A2B, req

    req = pending_request(user_b, user_a)
    if req and req.status == 0:
        return REL_B2A, req

    return REL_NONE, req

def relation(user_a, user_b):
    id, req = relation_and_request(user_a, user_b)
    return id

