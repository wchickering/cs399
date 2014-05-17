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

class Category(models.Model):
    company = models.ForeignKey(Company)
    description = models.CharField(max_length=200)
    def __unicode__(self):
        return self.description

class ProductCategory(models.Model):
    product = models.ForeignKey(Product)
    category = models.ForeignKey(Category)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.product), unicode(self.category))

class Concept(models.Model):
    company = models.ForeignKey(Company)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name

class ProductConcept(models.Model):
    product = models.ForeignKey(Product)
    concept = models.ForeignKey(Concept)
    value = models.FloatField()
    def __unicode__(self):
        return '%s = %0.2e' % (unicode(self.concept), self.value)

class Job(models.Model):
    category1 = models.ForeignKey(Category, related_name='category1')
    category2 = models.ForeignKey(Category, related_name='category2')
    pub_date = models.DateTimeField('date published')
    def __unicode__(self):
        return '%s : %s' % (unicode(self.category1), unicode(self.category2))
    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

class Poll(models.Model):
    job = models.ForeignKey(Job)
    product = models.ForeignKey(Product)
    def __unicode__(self):
        return unicode(self.product)

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    product = models.ForeignKey(Product)
    votes = models.IntegerField(default=0)
    def __unicode__(self):
        return unicode(self.product)
    
