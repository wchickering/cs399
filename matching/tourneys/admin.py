from django.contrib import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.db.models import Q

from tourneys.models import *

class LinkedInline(admin.TabularInline):
    module_name = None
    property_name = ['id']
    def details(self, instance):
        if self.module_name:
            module_name = self.module_name
        else:
            module_name = instance._meta.module_name
        ref = instance
        for name in self.property_name:
            ref = getattr(ref, name)
        url = reverse('admin:%s_%s_change' % (instance._meta.app_label,
                                              module_name),
                      args=(ref,))
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
        ('',                 {'fields': ['name']}),
        ('',                 {'fields': ['description']}),
    ]
    inlines = [AttributeInline, TournamentInline]
    list_display = ('name', 'description')
    list_display_links = ('name',)
    search_fields = ['name', 'description']
    # solution to FK filtering problem
    def change_view(self, request, object_id, extra_context=None):
        def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'team':
                league = League.objects.get(pk=object_id)
                kwargs['queryset'] = Team.objects\
                    .filter(~Q(attribute__in=league.attribute_set.all()))
            return super(TournamentInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        TournamentInline.formfield_for_foreignkey =\
            formfield_for_foreignkey
        return super(LeagueAdmin, self).change_view(request, object_id,
                                                    extra_context=extra_context)

admin.site.register(League, LeagueAdmin)

### Attribute ###

class TeamInline(LinkedInline):
   model = Team
   extra = 0

class AttributeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('',                {'fields': ['league']}),
        ('',                {'fields': ['name']}),
    ]
    inlines = [TeamInline]
    list_display = ('league', 'name')
    list_display_links = ('name',)
    list_filter = ['league']
    search_fields = ['name']

admin.site.register(Attribute, AttributeAdmin)

### Player ###

class PlayerAttributeInline(LinkedInline):
    model = PlayerAttribute
    extra = 0
    module_name = 'attribute'
    property_name = ['attribute', 'id']
    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

class PlayerAdmin(admin.ModelAdmin):
    fieldsets = [
        ('',                {'fields': ['league']}),
        ('',                {'fields': ['code']}),
        ('',                {'fields': ['description']}),
        ('',                {'fields': ['image', 'admin_image_tag']}),
    ]
    readonly_fields = ('admin_image_tag',)
    inlines = [PlayerAttributeInline]
    list_display = ('league', 'code', 'description', 'admin_image_tag')
    list_display_links = ('description',)
    list_filter = ['league']
    search_fields = ['code', 'description']
    # solution to FK filtering problem
    def change_view(self, request, object_id, extra_context=None):
        def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'attribute':
                player = Player.objects.get(pk=object_id)
                kwargs['queryset'] =\
                    Attribute.objects.filter(league=player.league)
            return super(PlayerAttributeInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        PlayerAttributeInline.formfield_for_foreignkey =\
            formfield_for_foreignkey
        return super(PlayerAdmin, self).change_view(request, object_id,
                                                    extra_context=extra_context)

admin.site.register(Player, PlayerAdmin)

### Team ###

class TeamPlayerInline(admin.TabularInline):
    model = TeamPlayer
    extra = 1
    readonly_fields = ('admin_image_tag',)

class TeamAdmin(admin.ModelAdmin):
    fieldsets = [
        ('',               {'fields': ['league']}),
        ('',               {'fields': ['name']}),
        ('',               {'fields': ['attribute']}),
        ('',               {'fields': ['positive']}),
        ('',               {'fields': ['playercount']}),
    ]
    readonly_fields = ('league', 'playercount')
    inlines = [TeamPlayerInline]
    list_display = ('league', 'name', 'attribute', 'positive', 'playercount')
    list_display_links = ('name',)
    search_fields = ['attribute__league__name', 'name', 'attribute__name']
    # solution to FK filtering problem
    def change_view(self, request, object_id, extra_context=None):
        def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'player':
                team = Team.objects.get(pk=object_id)
                kwargs['queryset'] = Player.objects\
                    .filter(league=team.attribute.league)
            return super(TeamPlayerInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        TeamPlayerInline.formfield_for_foreignkey =\
            formfield_for_foreignkey
        return super(TeamAdmin, self).change_view(request, object_id,
                                                  extra_context=extra_context)

admin.site.register(Team, TeamAdmin)

### Tournament ###

class TournamentTeamInline(LinkedInline):
    model = TournamentTeam
    extra = 0
    module_name = 'team'
    property_name = ['team', 'id']

class CompetitionInline(LinkedInline):
    model = Competition
    extra = 0
    readonly_fields = ('team',) + LinkedInline.readonly_fields

class TournamentAdmin(admin.ModelAdmin):
    fieldsets = [
        ('',                {'fields': ['league']}),
        ('',                {'fields': ['ttype']}),
        ('',                {'fields': ['name']}),
        ('Target',          {'fields': ['targetleague',
                                        'targetattribute',
                                        'targetteam']}),
        ('Parameters',      {'fields': ['num_players',
                                        'num_matches']}),
        ('State',           {'fields': ['round',
                                        'finished']}),
    ]
    readonly_fields = ('targetattribute', 'targetleague')
    inlines = [TournamentTeamInline, CompetitionInline]
    list_display = ('league', 'ttype', 'name', 'targetteam', 'num_players',
                    'num_matches', 'round', 'finished')
    list_display_links = ('name',)
    list_filter = ['league', 'ttype', 'num_players', 'num_matches', 'finished']
    search_fields = ['league__name', 'name', 'targetteam__name']
    # solution to FK filtering problem
    def change_view(self, request, object_id, extra_context=None):
        def tt_formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'team':
                tournament = Tournament.objects.get(pk=object_id)
                kwargs['queryset'] = Team.objects\
                    .filter(attribute__in=tournament.league.attribute_set.all())
            return super(TournamentTeamInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        TournamentTeamInline.formfield_for_foreignkey =\
            tt_formfield_for_foreignkey
        def c_formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'next_competition':
                tournament = Tournament.objects.get(pk=object_id)
                kwargs['queryset'] = Competition.objects\
                    .filter(tournament=tournament)
            return super(CompetitionInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        CompetitionInline.formfield_for_foreignkey = c_formfield_for_foreignkey
        return super(TournamentAdmin, self)\
            .change_view(request, object_id, extra_context=extra_context)

admin.site.register(Tournament, TournamentAdmin)

### Competition ###

class CompetitionTeamInline(LinkedInline):
    model = CompetitionTeam
    extra = 0
    module_name = 'team'
    property_name = ['team', 'id']

class MatchInline(LinkedInline):
    model = Match
    extra = 0
    readonly_fields = ('admin_image_tag',) + LinkedInline.readonly_fields

class CompetitionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('',                {'fields': ['league']}),
        ('',                {'fields': ['team']}),
        ('',                {'fields': ['tournament']}),
        ('',                {'fields': ['round']}),
        ('',                {'fields': ['finished']}),
        ('',                {'fields': ['next_competition']}),
    ]
    readonly_fields = ('league','team')
    inlines = [CompetitionTeamInline, MatchInline]
    list_display = ('league', 'team', 'tournament', 'round', 'finished')
    list_display_links = ('team',)
    list_filter = ['tournament', 'round', 'finished']
    search_fields = ['tournament__name', 'tournament__team__name',
                     'tournament__league__name']
    # solution to FK filtering problem
    def change_view(self, request, object_id, extra_context=None):
        def ct_formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'team':
                competition = Competition.objects.get(pk=object_id)
                kwargs['queryset'] = Team.objects.filter(
                    tournamentteam__tournament=competition.tournament
                )
            return super(CompetitionTeamInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        CompetitionTeamInline.formfield_for_foreignkey =\
            ct_formfield_for_foreignkey
        def m_formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'teamplayer':
                competition = Competition.objects.get(pk=object_id)
                kwargs['queryset'] = TeamPlayer.objects\
                    .filter(team__exact=competition.tournament.targetteam)
            return super(MatchInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        MatchInline.formfield_for_foreignkey = m_formfield_for_foreignkey
        return super(CompetitionAdmin, self)\
            .change_view(request, object_id, extra_context=extra_context)

admin.site.register(Competition, CompetitionAdmin)

### Match ###

class CompetitorInline(admin.TabularInline):
    model = Competitor
    extra = 0
    readonly_fields = ('admin_image_tag',)

class MatchAdmin(admin.ModelAdmin):
    fieldsets = [
        ('',                {'fields': ['competition']}),
        ('',                {'fields': ['teamplayer']}),
        ('',                {'fields': ['admin_image_tag']}),
        ('',                {'fields': ['finished']}),
    ]
    readonly_fields = ('admin_image_tag',)
    inlines = [CompetitorInline]
    list_display = ('competition', 'teamplayer', 'admin_image_tag', 'finished')
    list_display_links = ('teamplayer',)
    search_fields = ['competition__tournament__name', 'teamplayer__team__name',
                     'teamplayer__player__description']
    # solution to FK filtering problem
    def change_view(self, request, object_id, extra_context=None):
        def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
            if db_field.name == 'teamplayer':
                match = Match.objects.get(pk=object_id)
                kwargs['queryset'] = TeamPlayer.objects\
                    .filter(team__in=[ct.team for ct in\
                        match.competition.competitionteam_set.all()])
            return super(CompetitorInline, self).formfield_for_foreignkey(
                db_field, request=request, **kwargs)
        CompetitorInline.formfield_for_foreignkey = formfield_for_foreignkey
        return super(MatchAdmin, self)\
            .change_view(request, object_id, extra_context=extra_context)

admin.site.register(Match, MatchAdmin)

