# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.functional import curry
from django.conf import settings
from logistics.apps.logistics.models import ContactRole
from rapidsms.models import Contact, Backend
from rapidsms.utils.modules import try_import
from rapidsms.contrib.messaging.utils import send_message



def all_contacts():
    return "Everyone", {"All Active Contacts": Contact.objects.filter(is_active=True)}

def all_contacts_with_backend(backend_name):
    return {"All %s Contacts" % backend_name: Contact.objects.filter(connection__backend__name=backend_name)}

def all_contacts_with_all_backends():
    r = {}
    for backend in Backend.objects.all():
        r.update(all_contacts_with_backend(backend))
    return "SMS Backends", r

def all_contacts_with_role(role):
    return {"All %ss" % role.name: Contact.objects.filter(role=role)}

def all_contacts_with_all_roles():
    r = {}
    for role in ContactRole.objects.all():
        r.update(all_contacts_with_role(role))
    return "Roles", r



def get_contact_generator_functions():
    """
    This is similar to the method used by alerts, but adapted for a dict.
    """
    if not hasattr(settings, "CONTACT_GROUP_GENERATORS"):
        groups = ["groupmessaging.views.all_contacts",
                  "groupmessaging.views.all_contacts_with_all_roles",
                  "groupmessaging.views.all_contacts_with_all_backends",
                  ]
    else:
        groups = settings.CONTACT_GROUP_GENERATORS

    fns = []
    for group in groups:

        mod = group[0:group.rindex(".")]
        contact_module = try_import(mod)

        if contact_module is None:
            raise Exception("Contact generator module %s is not defined." % mod)

        func = group[group.rindex(".") + 1:]
        if not hasattr(contact_module, func):
            raise Exception("No function %s in module %s." %
                            (mod, func))
        fns.append(getattr(contact_module, func))
    return fns

@login_required
def group_message(request):
    fns = {}
    fn_tree = []
    for f in get_contact_generator_functions():
        r = f()
        fn_tree.append({"name": r[0],
                        "groups": r[1]})
        fns.update(r[1])
    success_count = 0
    failures = []
    if request.method == 'POST':
        msg = request.POST.get("msg")
        contacts_param = request.POST.get("contact_set")
        if not msg:
            messages.error(request, "No message supplied.")
        elif not contacts_param:
            messages.error(request, "No contacts selected.")
        found = ""
        if not contacts_param in fns:
            messages.error(request, "Invalid contact set selection.")
        else:
            contacts = set(fns[contacts_param].filter(is_active=True))
            
            for contact in contacts:
                try:
                    send_message(contact.default_connection, msg)
                    success_count += 1
                except Exception, e:
                    failures.append(contact.name)

            if success_count:
                messages.success(request, "Sent message to %d people." % success_count)
            else:
                messages.warning(request, "Didn't send any messages.")
            if failures:
                messages.error(request, "Failed to send message to %d people (%s)" % (len(failures), ", ".join(failures)))

    return render_to_response("groupmessaging/group_message.html",
        {
            "contact_fns": fn_tree,
        },
        context_instance=RequestContext(request))
