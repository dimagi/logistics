from django import template
from datetime import datetime
register = template.Library()

@register.filter
def during_this_month(date):
    if date.month == datetime.now().month:
        return True
    return False

