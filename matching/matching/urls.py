from django.conf.urls import patterns, include, url
from django.contrib import admin

# local modules
import settings

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^tourneys/', include('tourneys.urls', namespace='tourneys')),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
