from django.urls import path

from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('login/', login, name="login"),
    path('register/', register, name="register"),
    path('complete_profile/', complete_profile, name="complete_profile"),

]
