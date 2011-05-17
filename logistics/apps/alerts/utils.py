from django.conf import settings
from rapidsms.utils.modules import try_import


def get_alert_functions():
    """
    Return a list of alert generators defined in the LOGISTICS_ALERT_GENERATORS
    setting.

    Return an empty list if no alert generators are defined.
    All exceptions raised while importing generators are
    allowed to propagate, to avoid masking errors.
    """

    alert_functions = []
    if not hasattr(settings, "LOGISTICS_ALERT_GENERATORS"):
        # TODO: should this fail harder?
        return []
        
    for alert_method in settings.LOGISTICS_ALERT_GENERATORS:
        mod = alert_method[0:alert_method.rindex(".")]
        alerts_module = try_import(mod)

        if alerts_module is None:
            raise Exception("Alerts module %s is not defined." % (mod))
                
        func = alert_method[alert_method.rindex(".") + 1:]
        if not hasattr(alerts_module, func):
            raise Exception("No function %s in module %s." %
                            (mod, func))
    
        alert_functions.append(getattr(alerts_module, func))
    
    return alert_functions


