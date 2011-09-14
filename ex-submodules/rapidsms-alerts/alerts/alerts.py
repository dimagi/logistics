from alerts import Alert

def empty(request):
    """
    Example method for adding alerts to your application. This one
    just returns a single empty alert.
    """
    return [Alert("To set custom alerts, you must configure your LOGISTICS_ALERT_GENERATORS settings variable")]
