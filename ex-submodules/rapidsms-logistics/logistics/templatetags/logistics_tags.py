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
    qd = request.GET.copy()
    qd[a] = b
    return "%s?%s" % (request.path, qd.urlencode())

def raw(parser, token):
    # ro: thanks to EveryBlock for this code snippet
    # Whatever is between {% raw %} and {% endraw %} will skip the cache
    # so that e.g. 'usernames' can be refreshed while reports remain cached
    text = []
    parse_until = 'endraw'
    tag_mapping = {
        template.TOKEN_TEXT: ('', ''),
        template.TOKEN_VAR: ('{{', '}}'),
        template.TOKEN_BLOCK: ('{%', '%}'),
        template.TOKEN_COMMENT: ('{#', '#}'),
    }
    # By the time this template tag is called, the template system has already
    # lexed the template into tokens. Here, we loop over the tokens until
    # {% endraw %} and parse them to TextNodes. We have to add the start and
    # end bits (e.g. "{{" for variables) because those have already been
    # stripped off in a previous part of the template-parsing process.
    while parser.tokens:
        token = parser.next_token()
        if token.token_type == template.TOKEN_BLOCK and token.contents == parse_until:
            return template.TextNode(u''.join(text))
        start, end = tag_mapping[token.token_type]
        text.append(u'%s%s%s' % (start, token.contents, end))
    parser.unclosed_block_tag(parse_until)
raw = register.tag(raw)
