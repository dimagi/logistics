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
