from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from pardakht import urls as pardakht_urls

from . import settings

admin.autodiscover()
urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', include('mainapp.urls')),
                  path('pay/online/', include(pardakht_urls)),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
