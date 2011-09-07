from django.core.urlresolvers import reverse
from django import template
register = template.Library()
    
@register.simple_tag
def contact(contact):
    context = {}
    context['phone'] = contact.phone if contact.phone else "no phone information"
    context['link'] = reverse('registration_edit', args=(contact.pk, ))
    context['name'] = contact.name
    return "<a href=\"%(link)s\">%(name)s (%(phone)s)</a></br>" % context

@register.simple_tag
def mp_prev_month_link(request, mp):
    qd = request.GET.copy()
    qd['month'] = mp.prev_month.month
    qd['year'] = mp.prev_month.year
    return "%s?%s" % (request.path, qd.urlencode())

@register.simple_tag
def mp_next_month_link(request, mp):
    qd = request.GET.copy()
    qd['month'] = mp.next_month.month
    qd['year'] = mp.next_month.year
    return "%s?%s" % (request.path, qd.urlencode())

@register.simple_tag
def url_get_replace(request, a, b):
    print a, b
    qd = request.GET.copy()
    qd[a] = b
    return "%s?%s" % (request.path, qd.urlencode())
