from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404, redirect
from models import Notification, NotificationComment
import json
from django.core.exceptions import SuspiciousOperation

def add_comment(request):
    alert_id = int(request.POST.get('alert_id'))
    text = request.POST.get('text')
    user = request.user
    if not user.is_authenticated():
        raise SuspiciousOperation('attempt to add comment w/o authenticated user')

    comment = NotificationComment(
        notification=Notification.objects.get(id=alert_id),
        user=user,
        text=text
    )
    comment.save()

    return HttpResponse(json.dumps(comment.json()), 'text/json')

def alert_action(request):
    alert_id = int(request.POST.get('alert_id'))
    action = request.POST.get('action')
    user = request.user
    if not user.is_authenticated():
        raise SuspiciousOperation('attempt to take action on alert w/o authenticated user')

    # factor this out somewhere
    alert = Notification.objects.get(id=alert_id)
    alert.owner = user
    alert.status = {'fu': 'fu', 'resolve': 'closed'}[action]
    alert.save()

    return HttpResponse(json.dumps(alert.json(user)), 'text/json')
