import json
import calendar
import itertools
from datetime import datetime, timedelta
from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def int_to_month(month_number):
    d = datetime(2010, month_number, 1)
    return d.strftime("%b")

@register.simple_tag
def int_to_day(day_number):
    return calendar.day_name[day_number]
    
@register.simple_tag
def js_int_to_month(month_number):
    """
    Convert a javascript integer to a month name.  Javascript months are 0
    indexed."""
    return int_to_month(month_number + 1)

@register.filter
def dict_lookup(dict, key):
    '''Get an item from a dictionary.'''
    return dict.get(key)
    
@register.filter
def array_lookup(array, index):
    '''Get an item from an array.'''
    if index < len(array):
        return array[index]
    
@register.filter
def attribute_lookup(obj, attr):
    '''Get an attribute from an object.'''
    if (hasattr(obj, attr)):
        return getattr(obj, attr)
    
