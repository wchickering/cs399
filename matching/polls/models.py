import datetime

from django.db import models
from django.utils import timezone

class Company(models.Model):
    shortname = models.CharField(max_length=20)
    longname = models.CharField(max_length=100)
    def __unicode__(self):
        return self.shortname

class Product(models.Model):
    company = models.ForeignKey(Company)
    item_id = models.IntegerField()
    url = models.TextField()
    description = models.TextField()
    def __unicode__(self):
        return self.description

class Poll(models.Model):
    product = models.ForeignKey(Product)
    pub_date = models.DateTimeField('date published')
    def __unicode__(self):
        return self.product
    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    product = models.ForeignKey(Product)
    votes = models.IntegerField(default=0)
    def __unicode__(self):
        return self.product
    
