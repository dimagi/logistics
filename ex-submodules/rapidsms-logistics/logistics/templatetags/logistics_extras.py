from django import template
from logistics.templatetags.math_tags import percent
register = template.Library()

@register.inclusion_tag("logistics/templatetags/highlight_months_available.html")
def highlight_months(stockonhand, media_url):
    return { "stockonhand": stockonhand, "MEDIA_URL":media_url }

@register.simple_tag
def percent_cell(a, b):
    val = percent(a, b)
    return '<td title="%(a)s of %(b)s">%(val)s</td>' % {"a": a, "b": b, "val": val}