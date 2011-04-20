from django import template
from django.template.loader import render_to_string
register = template.Library()

@register.simple_tag
def render_nav(geography, location):
    return render_to_string("logistics/partials/accordion_partial.html", {"geography": geography,
                                                                          "location": location})
    
