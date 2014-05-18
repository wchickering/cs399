from django.contrib import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse

from tourneys.models import *

class LinkedInline(admin.TabularInline):
    def details(self, instance):
        url = reverse('admin:%s_%s_change' % (instance._meta.app_label,
                                              instance._meta.module_name),
                      args=(instance.id,))
        return format_html(u'<a href="{}">Details</a>', url)
    def has_delete_permission(self, request, obj=None):
        return False
    readonly_fields = ('details',)

### League ###

class AttributeInline(LinkedInline):
    model = Attribute
    extra = 0

class TournamentInline(LinkedInline):
    model = Tournament
    extra = 0

class LeagueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name',             {'fields': ['name']}),
        ('Description',      {'fields': ['description']}),
    ]
    inlines = [AttributeInline, TournamentInline]
    list_display = ('name', 'description')
    list_display_links = ('name',)

admin.site.register(League, LeagueAdmin)

### Attribute ###

class TeamInline(LinkedInline):
   model = Team
   extra = 0

class AttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('League',          {'fields': ['league']}),
        ('Name',            {'fields': ['name']}),
    ]
    inlines = [TeamInline]
    list_display = ('league', 'name')
    list_display_links = ('name',)
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
    list_display = ('league', 'code', 'description', 'image_tag')
    list_display_links = ('description',)
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
        ('Name',           {'fields': ['name']}),
        ('Attribute',      {'fields': ['attribute']}),
        ('Positive?',      {'fields': ['positive']}),
    ]
    readonly_fields = ('league',)
    inlines = [TeamPlayerInline]
    list_display = ('league', 'name', 'attribute', 'positive')
    list_display_links = ('name',)
    list_filter = ['attribute']

admin.site.register(Team, TeamAdmin)

### Tournament ###

class CompetitionInline(LinkedInline):
    model = Competition
    extra = 0
    readonly_fields = ('team',) + LinkedInline.readonly_fields
    def has_add_permission(self, request, obj=None):
        return False

class TournamentAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name',            {'fields': ['name']}),
        ('Source League',   {'fields': ['league']}),
        ('Target Team',     {'fields': ['team']}),
        ('Target Attribute',{'fields': ['targetattribute']}),
        ('Target League',   {'fields': ['targetleague']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
    ]
    readonly_fields = ('targetattribute', 'targetleague')
    inlines = [CompetitionInline]
    list_display = ('league', 'name', 'team', 'round', 'finished')
    list_display_links = ('name',)
    list_filter = ['league', 'finished']
    search_fields = ['name', 'team']

admin.site.register(Tournament, TournamentAdmin)

### Competition ###

class CompetitionTeamInline(admin.TabularInline):
    model = CompetitionTeam
    extra = 0

class MatchInline(LinkedInline):
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
    list_display = ('league', 'team', 'tournament', 'round', 'finished')
    list_display_links = ('team',)
    list_filter = ['tournament', 'round', 'finished']

admin.site.register(Competition, CompetitionAdmin)

### Match ###

class CompetitorInline(admin.TabularInline):
    model = Competitor
    extra = 0

class MatchAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Competition',   {'fields': ['competition']}),
        ('Target Player',   {'fields': ['teamplayer']}),
    ]
    inlines = [CompetitorInline]
    list_display = ('competition', 'teamplayer')
    list_display_links = ('teamplayer',)

admin.site.register(Match, MatchAdmin)

