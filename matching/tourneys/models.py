import datetime
import os

from django.db import models
from django.utils import timezone

# analogous to a retailer
class League(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField()
    mediadir = models.CharField(max_length=20)
    def __unicode__(self):
        return self.name

# analogous to a concept
class Attribute(models.Model):
    league = models.ForeignKey(League)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name

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

# analogous to a productconcept
class PlayerAttribute(models.Model):
    player = models.ForeignKey(Player)
    attribute = models.ForeignKey(Attribute)
    value = models.FloatField()
    def __unicode__(self):
        return '%s = %0.2e' % (unicode(self.attribute), self.value)
    def league(self):
        return self.attribute.league

# an attribute (i.e. concept) in the context of tournaments
class Team(models.Model):
    attribute = models.ForeignKey(Attribute)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name
    def league(self):
        return self.attribute.league

# a player (i.e. product) in the context of a team
class TeamPlayer(models.Model):
    team = models.ForeignKey(Team)
    player = models.ForeignKey(Player)
    def __unicode__(self):
        return unicode(self.player)
    def league(self):
        return self.team.attribute.league
    def image_tag(self):
        return self.player.image_tag()
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True

# analogous to a MTurk job
class Tournament(models.Model):
    # league within which teams will compete
    league = models.ForeignKey(League)
    # foreign team being matched to
    team = models.ForeignKey(Team)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.league), unicode(self.team))
    def targetattribute(self):
        return self.team.attribute
    def targetleague(self):
        return self.targetattribute().league

# a competition between multiple source concepts to match a target concept
class Competition(models.Model):
    next_competition = models.ForeignKey('self', null=True)
    tournament = models.ForeignKey(Tournament)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return 'Rnd %d : %s' % (self.round, unicode(self.tournament))
    def league(self):
        return self.tournament.league
    def team(self):
        return self.tournament.team
    def targetleague(self):
        return self.tournament.targetleague()

# a team (i.e. concept) in the context of a competition
class CompetitionTeam(models.Model):
    competition = models.ForeignKey(Competition)
    team = models.ForeignKey(Team)
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return unicode(self.team)

# analogous to a task in MTurk
# a competition consists of several matches
class Match(models.Model):
    competition = models.ForeignKey(Competition)
    def __unicode__(self):
        return unicode(self.competition)

# a player (i.e. product) in the context of a match
class Competitor(models.Model):
    match = models.ForeignKey(Match)
    competitionteam = models.ForeignKey(CompetitionTeam)
    teamplayer = models.ForeignKey(TeamPlayer)
    winner = models.NullBooleanField()
    def __unicode__(self):
        return '%s (%s)' % (unicode(self.player), unicode(self.team))
    
