from django.contrib import admin
from tourneys.models import League, Attribute, Player, PlayerAttribute,\
                            Tournament, Competition, Competitor

class TournamentAsSourceInline(admin.TabularInline):
    model = Tournament
    fk_name = 'source_league'
    extra = 0

class TournamentAsTargetInline(admin.TabularInline):
    model = Tournament
    fk_name = 'target_league'
    extra = 0

class LeagueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name',             {'fields': ['name']}),
        ('Description',      {'fields': ['description']}),
    ]
    inlines = [TournamentAsSourceInline, TournamentAsTargetInline]

class PlayerAttributeInline(admin.TabularInline):
    model = PlayerAttribute
    extra = 0

class PlayerAdmin(admin.ModelAdmin):
    fieldsets = [
        ('League',          {'fields': ['league']}),
        ('Code',            {'fields': ['code']}),
        ('Description',     {'fields': ['description']}),
    ]
    inlines = [PlayerAttributeInline]

class CompetitionInline(admin.TabularInline):
    model = Competition
    extra = 0

class TournamentAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Source League',   {'fields': ['source_league']}),
        ('Target League',   {'fields': ['target_league']}),
        ('Attribute',       {'fields': ['attribute']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
    ]
    inlines = [CompetitionInline]
    list_filter = ['source_league', 'target_league', 'finished']

class CompetitorInline(admin.TabularInline):
    model = Competitor
    extra = 3

class CompetitionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Tournament',      {'fields': ['tournament']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
    ]
    inlines = [CompetitorInline]
    list_filter = ['tournament']

admin.site.register(League, LeagueAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Competition, CompetitionAdmin)
