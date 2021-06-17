from django.urls import path
from django.views.generic import RedirectView

from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('login/', login, name="login"),
    path('factor/', GetFactorView.as_view(), name="factor"),
    path('logout/', logout, name="logout"),
    path('register/', register, name="register"),
    # path('new_request/', new_request, name="new_request"),
    path('new_request/', RedirectView.as_view(pattern_name='index', permanent=False), name="new_request"),
    path('complete_profile/', complete_profile, name="complete_profile"),
    path('calc_cost/', calc_cost, name="calc_cost"),
    path('edit_profile/', edit_profile, name="edit_profile"),
    # path('extend/<slug:sn>', extend, name="extend"),
    path('extend/<slug:sn>', RedirectView.as_view(pattern_name='index', permanent=False), name="extend"),
    path('pay/<slug:sn>', pay, name="pay"),
    path('pay_extend/<slug:sn>', pay_extend, name="pay_extend"),
    path('pay_online/', pay_online, name="pay_online"),
    path('pay_online_extend/', pay_online_extend, name="pay_online_extend"),
    path('cancel/', cancel, name="cancel"),
    path('extend_requests/', extend_requests, name="extend_requests"),
    path('get_limits_based_on_os/', get_limits_based_on_os, name="get_limits_based_on_os"),
    path('dl/software/', software_list, name="software_list"),

]
