from django.contrib import admin
from polls.models import Company, Category, Concept, Product, ProductCategory,\
                         ProductConcept, Job, Poll, Choice

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 3

class CompanyAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Short name',       {'fields': ['shortname']}),
        ('Long name',        {'fields': ['longname']}),
    ]
    inlines = [CategoryInline]

class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 3

class CategoryAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Company',          {'fields': ['company']}),
        ('Description',      {'fields': ['description']}),
    ]
    inlines = [ProductCategoryInline]

class ProductConceptInline(admin.TabularInline):
    model = ProductConcept
    extra = 0

class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Company',         {'fields': ['company']}),
        ('ID',              {'fields': ['item_id']}),
        ('URL',             {'fields': ['url']}),
        ('Description',     {'fields': ['description']}),
    ]
    inlines = [ProductCategoryInline]
    inlines = [ProductConceptInline]

class PollInline(admin.TabularInline):
    model = Poll
    extra = 3

class JobAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Category1',         {'fields': ['category1']}),
        ('Category2',         {'fields': ['category2']}),
        ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    ]
    inlines = [PollInline]
    list_filter = ['pub_date', 'category1', 'category2']

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Job',              {'fields': ['job']}),
        ('Product',          {'fields': ['product']}),
    ]
    inlines = [ChoiceInline]
    list_filter = ['job']

admin.site.register(Company, CompanyAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Poll, PollAdmin)
