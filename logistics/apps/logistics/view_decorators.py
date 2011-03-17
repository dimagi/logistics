from django.shortcuts import get_object_or_404
from logistics.apps.logistics.models import Product, ProductType, Location, get_geography

def filter_context(func):
    """
    add commodities and commoditytypes to context
    """
    def _new_func(*args, **kwargs):
        context = {}
        context['commodities'] = Product.objects.all().order_by('name')
        context['commoditytypes'] = ProductType.objects.all().order_by('name')
        if 'context' in kwargs:
            kwargs['context'].update(context)
        else:
            kwargs['context'] = context
        return func(*args, **kwargs)
    return _new_func

def geography_context(func):
    """
    add geography to context
    """
    def _new_func(*args, **kwargs):
        context = {}
        context['geography'] = get_geography()
        if 'context' in kwargs:
            kwargs['context'].update(context)
        else:
            kwargs['context'] = context
        return func(*args, **kwargs)
    return _new_func