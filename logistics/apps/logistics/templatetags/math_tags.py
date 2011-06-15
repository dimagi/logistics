from django import template
from django.template.loader import render_to_string
register = template.Library()

@register.simple_tag
def divide(a, b):
    if b and b != 0:
        return float(a)/float(b)
    return "NaN"
        
@register.simple_tag
def multiply(a, b):
    return a*b
        
@register.simple_tag
def percent(a, b):
    d = divide(a, b)
    if d != "NaN":
        return "%.1f %%" % (d * 100)
    return d    
