import datetime
import os

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

# analogous to a retailer
class League(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    mediadir = models.CharField(max_length=20, verbose_name='Media Directory')
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

# analogous to a concept
class Attribute(models.Model):
    league = models.ForeignKey(League)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['league', 'name']
        unique_together = ('league', 'name')

# analogous to a product
class Player(models.Model):
    league = models.ForeignKey(League)
    code = models.CharField(max_length=100)
    description = models.TextField()
    def image_path(instance, filename):
       return os.path.join(instance.league.mediadir, filename)
    image = models.ImageField(upload_to=image_path)
    def __unicode__(self):
        return self.description
    def image_tag(self):
        return '<img src="%s"/>' % self.image.url
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    # a bit sketchy (couples model and admin app)
    def admin_image_tag(self):
        url = reverse('admin:%s_%s_change' % (self._meta.app_label,
                                              self._meta.module_name),
                      args=(self.id,))
        return '<a href="%s">%s</a>' % (url, self.image_tag())
    admin_image_tag.short_description = 'Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['league', 'code']
        unique_together = ('league', 'code')

# analogous to a productconcept
class PlayerAttribute(models.Model):
    player = models.ForeignKey(Player)
    attribute = models.ForeignKey(Attribute)
    value = models.FloatField()
    def __unicode__(self):
        return '%s : %s' % (unicode(self.player), unicode(self.attribute))
    def league(self):
        return self.attribute.league
    class Meta:
        ordering = ['player', 'attribute']
        unique_together = ('player', 'attribute')
    def clean(self):
        if self.player.league != self.attribute.league:
            raise ValidationError(
                ('Player League (%(playerleague)s) not equal to Attribute '
                 'League (%(attributeleague)s)'),
                params={'playerleague': self.player.league,
                        'attributeleague': self.attribute.league}
            )

# an attribute (i.e. concept) in the context of tournaments
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    attribute = models.ForeignKey(Attribute)
    positive = models.BooleanField(default=True, verbose_name='Positive?')
    def __unicode__(self):
        return self.name
    def league(self):
        return self.attribute.league
    def playercount(self):
        return self.teamplayer_set.count()
    playercount.short_description = 'Player Count'
    class Meta:
        ordering = ['name', 'attribute']

# a player (i.e. product) in the context of a team
class TeamPlayer(models.Model):
    team = models.ForeignKey(Team)
    player = models.ForeignKey(Player)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.team), unicode(self.player))
    def league(self):
        return self.team.attribute.league
    def image_tag(self):
        return self.player.image_tag()
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    def admin_image_tag(self):
        return self.player.admin_image_tag()
    admin_image_tag.short_description = 'Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['team', 'player']
        unique_together = ('team', 'player')
    def clean(self):
        if self.team.attribute.league != self.player.league:
            raise ValidationError(
                ('Team League (%(teamleague)s) not equal to Player '
                 'League (%(playerleague)s)'),
                params={'teamleague': self.team.attribute.league,
                        'playerleague': self.player.league}
            )

class TournamentType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

# analogous to a MTurk job
class Tournament(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ttype = models.ForeignKey(TournamentType, verbose_name='Tournament Type')
    # league within which teams will compete
    league = models.ForeignKey(League)
    # target team being matched to
    targetteam = models.ForeignKey(Team, related_name='targetteam',
                                   verbose_name='Target Team')
    num_players = models.PositiveSmallIntegerField()
    num_matches = models.PositiveSmallIntegerField()
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return self.name
    def targetattribute(self):
        return self.targetteam.attribute
    targetattribute.short_description = 'Target Attribute'
    def targetleague(self):
        return self.targetattribute().league
    targetleague.short_description = 'Target League'
    class Meta:
        ordering = ['name']
    def clean(self):
        if self.round == 0:
            raise ValidationError('Round must be finite.')
        # TODO: Perhaps we want to lift this constraint in order to run tests in
        # which we match attributes against themselves
        if self.league == self.targetteam.attribute.league:
            raise ValidationError(
                ('Source League (%(league)s) is equal to Target Team '
                 'League'),
                params={'league': self.league}
            )

# a team (i.e. concept) in the context of a tournament
class TournamentTeam(models.Model):
    tournament = models.ForeignKey(Tournament)
    team = models.ForeignKey(Team)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.tournament), unicode(self.team))
    class Meta:
        ordering = ['tournament', 'team']
        unique_together = ('tournament', 'team')
    def clean(self):
        if self.tournament.league != self.team.attribute.league:
            raise ValidationError(
                ('Tournament League (%(tournamentleague)s) not equal to '
                 'Team League (%(teamleague)s)'),
                params={'tournamentleague': self.tournament.league,
                        'teamleague': self.team.attribute.league}
            )

# a competition between multiple source concepts to match a target concept
class Competition(models.Model):
    tournament = models.ForeignKey(Tournament)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False, verbose_name='Finished?')
    next_competition = models.ForeignKey('self', null=True, blank=True)
    def __unicode__(self):
        return '%s (Rnd %d)' % (unicode(self.tournament), self.round)
    def league(self):
        return self.tournament.league
    def team(self):
        return self.tournament.targetteam
    team.short_description = 'Target Team'
    def attribute(self):
        return self.tournament.targetteam.attribute
    attribute.short_description = 'Team Attribute'
    def targetleague(self):
        return self.tournament.targetleague()
    targetleague.short_description = 'Target League'
    class Meta:
        ordering = ['tournament', 'round']
    def clean(self):
        if self.next_competition is not None:
            if self.next_competition.tournament != self.tournament:
                raise ValidationError(
                    ('Next competition tournament (%(nexttournary)s) not equal '
                     'to this competition tournament (%(thistourney)s)'),
                    params={'nexttourney': self.next_competition.tournament,
                            'thistourney': self.tournament}
                )
            if self.next_competition.round != self.round + 1:
                raise ValidationError(
                    ('Next competition round (%(nextround)u) not equal to '
                     'this competition round (%(thisround)u) plus one'),
                    params={'nextround': self.next_competition.round,
                            'thisround': self.round}
                )
        if self.finished:
            if self.competitionteam_set.count() != self.tournament.num_players:
                raise ValidationError(
                    ('Number of competitionteams not equal to '
                     'tournament.num_player for finished competition %d') %\
                     self.pk
                )
            if self.match_set.count() != self.tournament.num_matches:
                raise ValidationError(
                    ('Number of matches not equal to tournament.num_matches '
                     'for finished competition %d') % self.pk
                )

# a team (i.e. concept) in the context of a competition
class CompetitionTeam(models.Model):
    competition = models.ForeignKey(Competition)
    team = models.ForeignKey(Team)
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competition), unicode(self.team))
    class Meta:
        ordering = ['competition', 'team']
        unique_together = ('competition', 'team')
    def clean(self):
        if not self.competition.tournament.tournamentteam_set\
                                          .filter(team=self.team).exists():
            raise ValidationError(
                'Team (%(team)s) not in Tournament (%(tournament)s)',
                params={'team': self.team,
                        'tournament': self.competition.tournament}
            )

# analogous to a task in MTurk
# a competition consists of several matches
class Match(models.Model):
    competition = models.ForeignKey(Competition)
    teamplayer = models.ForeignKey(TeamPlayer,
                                   verbose_name='Target Team Player')
    finished = models.BooleanField(default=False, verbose_name='Finished?')
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competition), unicode(self.teamplayer))
    def image_tag(self):
        return self.teamplayer.image_tag()
    image_tag.short_description = 'Target Image'
    image_tag.allow_tags = True
    def admin_image_tag(self):
        return self.teamplayer.admin_image_tag()
    admin_image_tag.short_description = 'Target Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['competition', 'teamplayer']
    def clean(self):
        if self.competition.tournament.targetteam != self.teamplayer.team:
            raise ValidationError(
                ('Competition Team (%(competitionteam)s) not equal to '
                 'TeamPlayer Team (%(playerteam)s)'),
                params={
                    'competitionteam': self.competition.tournament.targetteam,
                    'playerteam': self.teamplayer.team
                }
            )
        if self.finished:
            if self.competitor_set.count() !=\
               self.competition.tournament.num_players:
                raise ValidationError(
                    ('Number of competitors not equal to tournament.num_payer '
                     'for finished match %d') % self.pk
                )

# a player (i.e. product) in the context of a match
class Competitor(models.Model):
    match = models.ForeignKey(Match)
    competitionteam = models.ForeignKey(CompetitionTeam,
                                        verbose_name='Competition Team')
    teamplayer = models.ForeignKey(TeamPlayer, verbose_name='Team Player')
    winner = models.NullBooleanField(verbose_name='Winner?')
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competitionteam),
                            unicode(self.teamplayer))
    def image_tag(self):
        return self.teamplayer.image_tag()
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    def admin_image_tag(self):
        return self.teamplayer.admin_image_tag()
    admin_image_tag.short_description = 'Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['match', 'competitionteam', 'teamplayer']
        # no duplicate players or teams in match
        unique_together = (('match', 'competitionteam'),
                           ('match', 'teamplayer'))
    def clean(self):
        if self.match.competition != self.competitionteam.competition:
            raise ValidationError(
                ('Match Competition (%(matchcompetition)s) not equal to '
                 'CompetitionTeam Competition (%(teamcompetition)s)'),
                params={'matchcompetition': self.match.competition,
                        'teamcompetition': self.competitionteam.competition}
            )
        if self.teamplayer.team != self.competitionteam.team:
            raise ValidationError(
                ('TeamPlayer Team (%(playerteam)s) not equal to '
                 'CompetitionTeam Team (%(teamteam)s)'),
                params={'playerteam': self.teamplayer.team,
                        'teamteam': self.competitionteam.team}
            )
    
