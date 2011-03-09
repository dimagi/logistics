from django import template
register = template.Library()

@register.inclusion_tag("logistics/templatetags/highlight_months_available.html")
def highlight(stockonhand):
    return { "stockonhand": stockonhand }
