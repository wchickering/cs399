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
        # TODO: Make this a bit less sketchy
        url = reverse('admin:%s_%s_change' % (self._meta.app_label,
                                              self._meta.module_name),
                      args=(self.id,))
        return '<a href="%s"><img src="%s"/></a>' % (url, self.image.url)
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
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
    def clean(self):
        if self.player.league.pk != self.attribute.league.pk:
            raise ValidationError(
                ('Player League (%(playerleague)s) not equal to Attribute '
                 'League (%(attributeleague)s)'),
                params={'playerleague': self.player.league,
                        'attributeleague': self.attribute.league}
            )
    class Meta:
        ordering = ['player', 'attribute']
        unique_together = ('player', 'attribute')

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
    def clean(self):
        if self.team.attribute.league.pk != self.player.league.pk:
            raise ValidationError(
                ('Team League (%(teamleague)s) not equal to Player '
                 'League (%(playerleague)s)'),
                params={'teamleague': self.team.attribute.league,
                        'playerleague': self.player.league}
            )
    class Meta:
        ordering = ['team', 'player']
        unique_together = ('team', 'player')

# analogous to a MTurk job
class Tournament(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # league within which teams will compete
    league = models.ForeignKey(League)
    # target team being matched to
    team = models.ForeignKey(Team, verbose_name='Target Team')
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return self.name
    def targetattribute(self):
        return self.team.attribute
    targetattribute.short_description = 'Target Attribute'
    def targetleague(self):
        return self.targetattribute().league
    targetleague.short_description = 'Target League'
    def clean(self):
        if self.round == 0:
            raise ValidationError('Round must be finite.')
        if self.league.pk == self.team.attribute.league.pk:
            raise ValidationError(
                ('Source League (%(league)s) is equal to Target Team '
                 'League'),
                params={'league': self.league}
            )
    class Meta:
        ordering = ['name']

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
        return self.tournament.team
    team.short_description = 'Target Team'
    def attribute(self):
        return self.tournament.team.attribute
    attribute.short_description = 'Team Attribute'
    def targetleague(self):
        return self.tournament.targetleague()
    targetleague.short_description = 'Target League'
    def clean(self):
        if self.next_competition is not None:
            if self.next_competition.tournament.pk != self.tournament.pk:
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
    class Meta:
        ordering = ['tournament', 'round']

# a team (i.e. concept) in the context of a competition
class CompetitionTeam(models.Model):
    competition = models.ForeignKey(Competition)
    team = models.ForeignKey(Team)
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competition), unicode(self.team))
    def clean(self):
        if self.competition.tournament.league.pk !=\
           self.team.attribute.league.pk:
            raise ValidationError(
                ('Competition League (%(competitionleague)s) not equal to '
                 'Team League (%(teamleague)s)'),
                params={'competitionleague': self.competition.tournament.league,
                        'teamleague': self.team.attribute.league}
            )
    class Meta:
        ordering = ['competition', 'team']
        unique_together = ('competition', 'team')

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
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    def clean(self):
        if self.competition.tournament.team.pk != self.teamplayer.team.pk:
            raise ValidationError(
                ('Competition Team (%(competitionteam)s) not equal to '
                 'TeamPlayer Team (%(playerteam)s)'),
                params={'competitionteam': self.competition.tournament.team,
                        'playerteam': self.teamplayer.team}
            )
        winner_count = 0
        for competitor in self.competitor_set.all():
            if competitor.winner:
                winner_count += 1
        if winner_count > 1:
            raise ValidationError('Match has multiple winners')
    class Meta:
        ordering = ['competition', 'teamplayer']

# a player (i.e. product) in the context of a match
class Competitor(models.Model):
    match = models.ForeignKey(Match)
    competitionteam = models.ForeignKey(CompetitionTeam,
                                        verbose_name='Competition Team')
    teamplayer = models.ForeignKey(TeamPlayer, verbose_name='Team Player')
    winner = models.NullBooleanField(verbose_name='Winner?')
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competitionteam),
                            unicode(self.teamplayer))
    def image_tag(self):
        return self.teamplayer.image_tag()
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    def clean(self):
        if self.match.competition.pk != self.competitionteam.competition.pk:
            raise ValidationError(
                ('Match Competition (%(matchcompetition)s) not equal to '
                 'CompetitionTeam Competition (%(teamcompetition)s)'),
                params={'matchcompetition': self.match.competition,
                        'teamcompetition': self.competitionteam.competition}
            )
        if self.teamplayer.team.pk != self.competitionteam.team.pk:
            raise ValidationError(
                ('TeamPlayer Team (%(playerteam)s) not equal to '
                 'CompetitionTeam Team (%(teamteam)s)'),
                params={'playerteam': self.teamplayer.team,
                        'teamteam': self.competitionteam.team}
            )
    class Meta:
        ordering = ['match', 'competitionteam', 'teamplayer']
        # no duplicate players or teams in match
        unique_together = (('match', 'competitionteam'),
                           ('match', 'teamplayer'))
    
