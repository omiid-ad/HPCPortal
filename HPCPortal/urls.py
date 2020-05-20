from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from pardakht import urls as pardakht_urls
from django.contrib.auth import views as auth_views

from . import settings

admin.autodiscover()
urlpatterns = [
                  path('panel/admin-site/', admin.site.urls),
                  path('', include('mainapp.urls')),
                  path('pay/online/', include(pardakht_urls)),
                  path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
                  path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
                  path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
                       name='password_reset_confirm'),
                  path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
