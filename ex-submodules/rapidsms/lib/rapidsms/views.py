from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout


@require_GET
def dashboard(request):
    return render(request, "dashboard.html")


def login(request, template_name="rapidsms/login.html"):
    return django_login(request, template_name=template_name)


def logout(request, template_name="rapidsms/loggedout.html"):
    return django_logout(request, template_name=template_name)
