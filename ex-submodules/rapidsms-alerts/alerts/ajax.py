from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404, redirect
from models import Notification, NotificationComment, user_name
import json
from django.core.exceptions import SuspiciousOperation

def add_comment(request):
    alert_id = int(request.POST.get('alert_id'))
    text = request.POST.get('text')
    user = request.user
    if not user.is_authenticated():
        raise SuspiciousOperation('attempt to add comment w/o authenticated user')

    comment = add_user_comment(Notification.objects.get(id=alert_id), user, text)
    return HttpResponse(json.dumps(comment.json()), 'text/json')

def alert_action(request):
    alert_id = int(request.POST.get('alert_id'))
    action = request.POST.get('action')
    action_comment = request.POST.get('comment')
    user = request.user
    if not user.is_authenticated():
        raise SuspiciousOperation('attempt to take action on alert w/o authenticated user')

    alert = Notification.objects.get(id=alert_id)
    {
        'fu': lambda a: a.followup(user),
        'esc': lambda a: a.escalate(),
        'resolve': lambda a: a.resolve(),
    }[action](alert)
    alert.save()

    if action_comment:
        add_user_comment(alert, user, action_comment)

    comment = NotificationComment(
        notification=alert,
        user=None,
        text=action_caption(action, alert, user)
    )
    comment.save()

    #simulated delay
    #import time
    #time.sleep(1.)

    return HttpResponse(json.dumps(alert.json(user)), 'text/json')

def action_caption(action, alert, user):
    username = user_name(user)
    if action == 'fu':
        if alert.status == 'esc':
            return '%s claimed the escalated issue' % username
        else:
            return '%s is following up' % username
    elif action == 'esc':
        return '%s escalated the issue to %s' % (username, alert.escalation_level_name(alert.escalation_level)) # alert will have already been escalated
    elif action == 'resolve':
        return '%s resolved the issue' % username

def add_user_comment(alert, user, text):
    comment = NotificationComment(
        notification=alert,
        user=user,
        text=text
    )
    comment.save()
    return comment
