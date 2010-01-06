from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, password_change

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('myproject',
    (r'^$', 'smski.views.index'),
    (r'^new_user/$', 'smski.views.new_user'),
    (r'^user_list/$', 'smski.views.users'),
    (r'^send_message/$', 'smski.views.send'),
    (r'^set_phone/$', 'smski.views.set_phone'),
    (r'^verify_phone/$', 'smski.views.verify_phone'),
    (r'^friend_request/(?P<user_id>\d+)/$', 'smski.views.friend_request'),
    (r'^logs/$', 'smski.views.logs'),
    (r'^account/$', 'smski.views.account'),
    (r'^account/(?P<user_id>\d+)/$', 'smski.views.account'),

    (r'^accounts/login/$',  login,  {"template_name": "login.html", "redirect_field_name":"next"}),
    (r'^accounts/logout/$', logout, {"next_page":"/"}),
    (r'^accounts/change_pw/$', password_change, {'template_name':'change_pw.html', 'post_change_redirect':'/accounts/changed/'}),
    (r'^accounts/changed/$', 'smski.views.show', {'template':'changed_pw.html'}),
    (r'^accounts/reset_pw/$', 'smski.views.reset_pw'),
    (r'^accounts/reset/$', 'smski.views.show', {'template':'reset.html'}),
)

