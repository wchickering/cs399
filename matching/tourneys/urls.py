from django.conf.urls import patterns, url

from tourneys import views

urlpatterns = patterns('',
    url(r'^$', views.match, name='match'),
    url(r'^(?P<match_id>[0-9]+)/matchsubmit/$', views.matchsubmit,
        name='matchsubmit')
)
