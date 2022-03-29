from __future__ import unicode_literals
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.contrib import messages

from logistics.decorators import place_in_request

from logistics_project.apps.malawi.warehouse.report_utils import datespan_default,\
    table_to_csv

from logistics_project.apps.malawi.warehouse.report_views import dashboard, emergency_orders,\
    order_fill_rates, resupply_qts_required, alert_summary, consumption_profiles, stock_status,\
    lead_times, reporting_rate, user_profiles, hsas, health_facilities, ad_hoc
from logistics_project.apps.malawi.util import get_or_create_user_profile
from logistics.util import config
from logistics_project.utils.parsing import string_to_boolean
import logging


reports_slug_map = {
    'dashboard': dashboard,
    'emergency-orders': emergency_orders,
    'order-fill-rate': order_fill_rates,
    're-supply-qts-required': resupply_qts_required,
    'alert-summary': alert_summary,
    'consumption-profiles': consumption_profiles,
    'stock-status': stock_status,
    'lead-times': lead_times,
    'reporting-rate': reporting_rate,
    'user-profiles': user_profiles,
    'hsas': hsas,
    'health-facilities': health_facilities,
    'ad-hoc': ad_hoc,
}



@place_in_request()
@datespan_default
def get_report(request, slug=''):
    return _get_report(request, slug, config.BaseLevel.HSA)


@place_in_request()
@datespan_default
def get_facility_report(request, slug=''):
    return _get_report(request, slug, config.BaseLevel.FACILITY)


def _set_base_level_info_on_request(request, base_level):
    request.base_level = base_level
    request.base_level_is_hsa = (base_level == config.BaseLevel.HSA)
    request.base_level_is_facility = (base_level == config.BaseLevel.FACILITY)


def _get_report(request, slug, base_level):
    _set_base_level_info_on_request(request, base_level)

    report = reports_slug_map[slug].View(slug)
    if not report.can_view(request):
        messages.warning(request,
                         "It looks like you don't have permission to access that view. "
                         "You've been redirected home.")
        return home(request)
    try:
        if getattr(report, 'automatically_adjust_datespan', False):
            report.update_datespan(request)
        # bit of a hack: for csv expect two these two magic params 
        # and pull the data from the context
        if string_to_boolean(request.GET.get("export_csv", "false")):
            table_id = request.GET.get('table')
            context = report.get_context(request)
            def _find_table(context, table_id):
                for k, v in list(context.items()):
                    if isinstance(v, dict) and v.get('id') == table_id:
                        return v
            table = _find_table(context, table_id)
            if table:
                return table_to_csv(table)
            else:
                messages.error(request, "Sorry, we can't find that table to export.")
        
        return report.get_response(request)
    except Exception as e:
        if settings.DEBUG:
            raise
        logging.exception("problem loading a warehouse view: %s" % e)
        messages.warning(request,
                         "It looks like there's no data for your filters. "
                         "You've been redirected.")
        return home(request)


def default_landing(request):
    profile = get_or_create_user_profile(request.user)
    if profile.current_dashboard_base_level == config.BaseLevel.HSA:
        return HttpResponseRedirect(reverse('malawi_hsa_dashboard'))
    elif profile.current_dashboard_base_level == config.BaseLevel.FACILITY:
        return HttpResponseRedirect(reverse('malawi_facility_dashboard'))
    else:
        raise Http404()


@place_in_request()
@datespan_default
def home(request):
    return _home(request, config.BaseLevel.HSA)


@place_in_request()
@datespan_default
def facility_home(request):
    return _home(request, config.BaseLevel.FACILITY)


def _home(request, base_level):
    _set_base_level_info_on_request(request, base_level)
    try:
        report = reports_slug_map["dashboard"].View("dashboard")
        assert report.can_view(request)
        return report.get_response(request)
    except Exception:
        if settings.DEBUG:
            raise
        return render(request, "%s/no-data.html" % settings.REPORT_FOLDER)
