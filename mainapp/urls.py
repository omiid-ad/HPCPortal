from django.urls import path

from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('login/', login, name="login"),
    path('logout/', logout, name="logout"),
    path('register/', register, name="register"),
    path('new_request/', new_request, name="new_request"),
    path('complete_profile/', complete_profile, name="complete_profile"),

]
