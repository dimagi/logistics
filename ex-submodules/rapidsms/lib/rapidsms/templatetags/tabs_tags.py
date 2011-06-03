#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import re
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Variable

register = template.Library()


class Tab(object):
    
    def __init__(self, view, caption=None, permission=None):
        self._caption = caption
        self._view = view
        self._permission = permission
    
    def _auto_caption(self):
        func_name = self._view.split('.')[-1]       # my_view
        return func_name.replace("_", " ").title()  # My View

    @property
    def url(self):
        """
        Return the URL of this tab.

        Warning: If this tab's view function cannot be reversed, Django
        will silently ignore the exception, and return the value of the
        TEMPLATE_STRING_IF_INVALID setting.
        """
        return reverse(self._view)

    @property
    def caption(self):
        return self._caption or self._auto_caption()

    @property
    def caption_slug(self):
        slug = self.caption.lower().replace(' ', '-') # convert spaces to '-'
        slug = re.sub(r'\W', '', slug) # remove any remaining non-word chars
        return slug

    def has_permission(self, user):
        if self._permission:    return user.has_perm(self._permission)
        else:                   return True


# adapted from ubernostrum's django-template-utils. it didn't seem
# substantial enough to add a dependency, so i've just pasted it.
class TabsNode(template.Node):
    def __init__(self, tabs, varname):
        self.tabs = tabs
        self.varname = varname
        
    def render(self, context):
        # try to find a request variable, but don't blow up entirely if we don't find it
        # (this no blow up property is mostly used during testing)
        try:
            request = Variable("request").resolve(context)
        except Exception as e:
            return ""

        for tab in self.tabs:
            tab.is_active = request.get_full_path().startswith(tab.url)
            tab.visible = tab.has_permission(request.user)                    
        
        context[self.varname] = self.tabs
        return ""


@register.tag
def get_tabs(parser, token):
    """
    Retrive a list of the tabs for this project, and store them in a
    named context variable. Returns nothing, via `ContextUpdatingNode`.

    Syntax::
        {% get_tabs as [varname] %}

    Example::
        {% get_tabs as tabs %}
        
    Looks for a RAPIDSMS_TABS value in settings.py formatted like:
    
    RAPIDSMS_TABS = [
        ("rapidsms.contrib.messagelog.views.message_log",       "Message Log", "is_superuser"),
        ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),
    ]
    
    The third value in the tuple (permission required) is optional.
    """

    args = token.contents.split()
    tag_name = args.pop(0)

    if len(args) != 2:
        raise template.TemplateSyntaxError(
            "The {%% %s %%} tag requires two arguments" % (tag_name))

    if args[0] != "as":
        raise template.TemplateSyntaxError(
            'The second argument to the {%% %s %%} tag must be "as"' %
            (tag_name))

    tabs = [Tab(*tab_args) for tab_args in settings.RAPIDSMS_TABS]
    return TabsNode(tabs, str(args[1]))