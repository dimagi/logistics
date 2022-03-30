from __future__ import unicode_literals
from django import template
register = template.Library()


@register.inclusion_tag('rapidsms/templatetags/form.html')
def render_form(form):
    return { "form": form }
