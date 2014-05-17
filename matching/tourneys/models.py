import datetime

from django.db import models
from django.utils import timezone

class League(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField()
    def __unicode__(self):
        return self.name

class Attribute(models.Model):
    league = models.ForeignKey(League)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return '%s (%s)' % (self.name, unicode(self.league))

class Player(models.Model):
    league = models.ForeignKey(League)
    code = models.IntegerField()
    description = models.TextField()
    def __unicode__(self):
        return self.description

class PlayerAttribute(models.Model):
    player = models.ForeignKey(Player)
    attribute = models.ForeignKey(Attribute)
    value = models.FloatField()
    def __unicode__(self):
        return '%s = %0.2e' % (unicode(self.attribute), self.value)

class Tournament(models.Model):
    league = models.ForeignKey(League)
    attribute = models.ForeignKey(Attribute)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.league), unicode(self.attribute))

class Competition(models.Model):
    tournament = models.ForeignKey(Tournament)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return 'Rnd %d : %s' % (self.round, unicode(self.tournament))

class Competitor(models.Model):
    competition = models.ForeignKey(Competition)
    player = models.ForeignKey(Player)
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return unicode(self.player)
    
