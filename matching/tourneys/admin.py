from django.contrib import admin
from tourneys.models import League, Attribute, Player, PlayerAttribute,\
                            Tournament, Competition, Competitor

class TournamentInline(admin.TabularInline):
    model = Tournament
    extra = 0

class LeagueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name',             {'fields': ['name']}),
        ('Description',      {'fields': ['description']}),
    ]
    inlines = [TournamentInline]

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
    list_display = ('league', 'code', 'description')
    list_filter = ['league']
    search_fields = ['code', 'description']

class CompetitionInline(admin.TabularInline):
    model = Competition
    extra = 0

class TournamentAdmin(admin.ModelAdmin):
    fieldsets = [
        ('League',          {'fields': ['league']}),
        ('Target Attribute',{'fields': ['attribute']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
    ]
    inlines = [CompetitionInline]
    list_display = ('league', 'attribute', 'round', 'finished')
    list_filter = ['league', 'finished']

class CompetitorInline(admin.TabularInline):
    model = Competitor
    extra = 0

class CompetitionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Tournament',      {'fields': ['tournament']}),
        ('Round',           {'fields': ['round']}),
        ('Finished?',       {'fields': ['finished']}),
    ]
    inlines = [CompetitorInline]
    list_filter = ['tournament', 'round', 'finished']

admin.site.register(League, LeagueAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Competition, CompetitionAdmin)
