from django.contrib import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse

from tourneys.models import *

class MyInline(admin.TabularInline):
    def details(self, instance):
        url = reverse('admin:%s_%s_change' % (instance._meta.app_label,
                                              instance._meta.module_name),
                      args=(instance.id,))
        return format_html(u'<a href="{}">Details</a>', url)
    def has_delete_permission(self, request, obj=None):
        return False
    readonly_fields = ('details',)

### League ###

class AttributeInline(MyInline):
    model = Attribute
    extra = 0

class TournamentInline(MyInline):
    model = Tournament
    extra = 0

class LeagueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name',             {'fields': ['name']}),
        ('Description',      {'fields': ['description']}),
    ]
    inlines = [AttributeInline, TournamentInline]

admin.site.register(League, LeagueAdmin)

### Attribute ###

class TeamInline(MyInline):
   model = Team
   extra = 0

class AttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('League',          {'fields': ['league']}),
        ('Name',            {'fields': ['name']}),
    ]
    inlines = [TeamInline]
    list_filter = ['league', 'name']

admin.site.register(Attribute, AttributeAdmin)

### Player ###

class PlayerAttributeInline(admin.TabularInline):
    model = PlayerAttribute
    extra = 0
    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

class PlayerAdmin(admin.ModelAdmin):
    fieldsets = [
        ('League',          {'fields': ['league']}),
        ('Code',            {'fields': ['code']}),
        ('Description',     {'fields': ['description']}),
        ('Image',           {'fields': ['image']}),
        ('',                {'fields': ['image_tag']}),
    ]
    readonly_fields = ('image_tag',)
    inlines = [PlayerAttributeInline]
    list_display = ('code', 'league', 'description', 'image_tag')
    list_filter = ['league']
    search_fields = ['code', 'description']

admin.site.register(Player, PlayerAdmin)

### Team ###

class TeamPlayerInline(admin.TabularInline):
    model = TeamPlayer
    extra = 1
    readonly_fields = ('image_tag',)

class TeamAdmin(admin.ModelAdmin):
    fieldsets = [
        ('League',         {'fields': ['league']}),
        ('Attribute',      {'fields': ['attribute']}),
    ]
    readonly_fields = ('league',)
    inlines = [TeamPlayerInline]
    list_display = ('attribute', 'league')
    list_filter = ['attribute']

admin.site.register(Team, TeamAdmin)

### Tournament ###

class CompetitionInline(MyInline):
    model = Competition
    extra = 0

class TournamentAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Source League',   {'fields': ['league']}),
        ('Target Team',     {'fields': ['team']}),
        ('Target Attribute',{'fields': ['targetattribute']}),
        ('Target League',   {'fields': ['targetleague']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
    ]
    readonly_fields = ('targetattribute', 'targetleague')
    inlines = [CompetitionInline]
    list_display = ('team', 'league', 'round', 'finished')
    list_filter = ['league', 'finished']

admin.site.register(Tournament, TournamentAdmin)

### Competition ###

class CompetitionTeamInline(MyInline):
    model = Team
    extra = 0

class MatchInline(admin.TabularInline):
    model = Match
    extra = 0

class CompetitionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Source League',   {'fields': ['league']}),
        ('Target Team',     {'fields': ['team']}),
        ('Tournament',      {'fields': ['tournament']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
        ('Next Competition',{'fields': ['next_competition']}),
    ]
    readonly_fields = ('league','team')
    inlines = [CompetitionTeamInline, MatchInline]
    list_filter = ['tournament', 'round', 'finished']

admin.site.register(Competition, CompetitionAdmin)

### CompetitionTeam ###

class CompetitorInline(admin.TabularInline):
    model = Competitor
    extra = 0

class CompetitionTeamAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Competition',    {'fields': ['competition']}),
        ('Team',           {'fields': ['team']}),
        ('Score',          {'fields': ['score']}),
    ]
    inlines = [CompetitorInline]
    list_filter = ['team']

admin.site.register(CompetitionTeam, CompetitionTeamAdmin)

