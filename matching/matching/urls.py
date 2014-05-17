from django.conf.urls import patterns, include, url
from django.contrib import admin

# local modules
import settings

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'matching.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^tourneys/', include('tourneys.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
