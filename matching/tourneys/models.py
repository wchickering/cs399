import datetime

from django.db import models
from django.utils import timezone

from smart_selects.db_fields import ChainedForeignKey

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
    league = models.ForeignKey(League)
    player = ChainedForeignKey(
        Player,
        chained_field='league',
        chained_model_field='league',
        show_all=False
    )
    attribute = ChainedForeignKey(
        Attribute,
        chained_field='league',
        chained_model_field='league',
        show_all=False
    )
    value = models.FloatField()
    def __unicode__(self):
        return '%s = %0.2e' % (unicode(self.attribute), self.value)

class Tournament(models.Model):
    source_league = models.ForeignKey(League, related_name='source_league')
    target_league = models.ForeignKey(League, related_name='target_league')
    attribute = ChainedForeignKey(
        Attribute,
        chained_field='target_league',
        chained_model_field='league',
        show_all=False
    )
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField()
    def __unicode__(self):
        return '%s : %s' % (unicode(self.source_league), unicode(self.attribute))

class Competition(models.Model):
    tournament = models.ForeignKey(Tournament)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField()

class Competitor(models.Model):
    competition = models.ForeignKey(Competition)
    player = models.ForeignKey(Player)
    score = models.FloatField(null=True)
    def __unicode__(self):
        return unicode(self.player)
    
