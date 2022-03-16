from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from rapidsms.utils.pagination import paginated
from rapidsms.contrib.ajax.utils import call_router

from .models import EventSchedule
from .forms import ScheduleForm


@login_required
def index(request, template="scheduler/index.html"):
    context = {}
    schedules = EventSchedule.objects.all()
    context['schedules'] = paginated(request, schedules)
    return render(request, template, context)


@login_required
def edit(request, pk, template="scheduler/edit.html"):
    context = {}
    schedule = get_object_or_404(EventSchedule, id=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            context['status'] = _("Schedule '%(name)s' successfully updated" % \
                                {'name':schedule.callback} )
        else:
            context['errors'] = form.errors
    else:
        form = ScheduleForm(instance=schedule)
    context['form'] = form
    context['schedule'] = schedule
    return render(request, template, context)


@require_POST
def test_schedule(request, schedule_pk):
    post = {"schedule_pk": schedule_pk}
    succeed = call_router("scheduler", "run_schedule", **post)
    return HttpResponseRedirect(reverse('scheduler'))
