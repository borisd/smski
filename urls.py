from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('myproject',
    (r'^$', 'smski.views.index'),
    (r'^new_user/$', 'smski.views.new_user'),
    (r'^user_list/$', 'smski.views.users'),
    (r'^send_message/$', 'smski.views.send'),
    (r'^accounts/login/$',  login,  {"template_name": "login.html", "redirect_field_name":"next"}),
    (r'^accounts/logout/$', logout, {"next_page":"/"}),
    (r'^set_phone/$', 'smski.views.set_phone'),
    (r'^verify_phone/$', 'smski.views.verify_phone'),
    (r'^friend_request/(?P<user_id>\d+)/$', 'smski.views.friend_request'),
    (r'^logs/$', 'smski.views.logs'),
)

