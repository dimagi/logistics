from django import template
register = template.Library()

@register.inclusion_tag("logistics/templatetags/highlight_months_available.html")
def highlight_months(stockonhand, media_url):
    return { "stockonhand": stockonhand, "MEDIA_URL":media_url }
