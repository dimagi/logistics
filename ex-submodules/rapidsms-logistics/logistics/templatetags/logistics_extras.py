from __future__ import unicode_literals
from django import template
from django.utils.safestring import mark_safe

from logistics.templatetags.math_tags import percent
register = template.Library()

@register.inclusion_tag("logistics/templatetags/highlight_months_available.html")
def highlight_months(stockonhand, static_url):
    return {
        "stockonhand": stockonhand,
        "STATIC_URL": static_url,
    }


@register.simple_tag
def percent_cell(a, b):
    val = percent(a, b)
    return mark_safe('<td title="%(a)s of %(b)s">%(val)s</td><td>%(b)s</td>' % {"a": a, "b": b, "val": val})

@register.filter('klass')
def klass(ob):
    return ob.__class__.__name__

@register.filter
def historical_date_last_stocked(productstock, date):
    return productstock.date_last_stocked(date)

@register.filter
def times(a,b):
    return a * b

@register.filter
def dict_lookup(dict, key):
    '''Get an item from a dictionary.'''
    return dict.get(key)
    
@register.filter
def array_lookup(array, index):
    '''Get an item from an array.'''
    if index < len(array):
        return array[index]
    
