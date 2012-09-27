from django.shortcuts import get_object_or_404
from rapidsms.conf import settings
from logistics.models import Product, ProductType, Location, get_geography

def filter_context(func):
    """
    add commodities and commoditytypes to context
    """
    def _new_func(request, *args, **kwargs):
        context = {}
        
        # add commodities 
        context['commodities'] = Product.objects.all().order_by('name')
        context['commoditytypes'] = ProductType.objects.all().order_by('name')
        context['commodity_filter'] = context['commoditytype_filter'] = None
        
        commodity_filter = None
        commoditytype_filter = None
    
        # add/set filters
        if hasattr(request,'REQUEST'):
            if 'commodity' in request.REQUEST:
                if request.REQUEST['commodity'] != 'all':
                    commodity_filter = request.REQUEST['commodity']
                    commoditytype_filter = Product.objects.get(sms_code=commodity_filter).type.code
                request.session['commodity_filter'] = commodity_filter
                request.session['commoditytype_filter'] = commoditytype_filter
            elif 'commoditytype' in request.REQUEST:
                if request.REQUEST['commoditytype'] != 'all':
                    commoditytype_filter = request.REQUEST['commoditytype']
                    type = ProductType.objects.get(code=commoditytype_filter)
                    context['commodities'] = context['commodities'].filter(type=type)
                request.session['commodity_filter'] = commodity_filter
                request.session['commoditytype_filter'] = commoditytype_filter
        if 'commodity_filter' in request.session:
            context['commodity_filter'] = request.session['commodity_filter']
        if 'commoditytype_filter' in request.session:
            context['commoditytype_filter'] = request.session['commoditytype_filter']

        if 'context' in kwargs:
            kwargs['context'].update(context)
        else:
            kwargs['context'] = context
        
        return func(request, *args, **kwargs)
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

def location_context(func):
    """
    add geography to context
    """
    def _new_func(*args, **kwargs):
        context = {}
        location_code = settings.COUNTRY
        if 'location_code' in kwargs:
            location_code = kwargs['location_code']
        location = get_object_or_404(Location, code=location_code)
        context['location'] = location
        if 'context' in kwargs:
            kwargs['context'].update(context)
        else:
            kwargs['context'] = context
        return func(*args, **kwargs)
    return _new_func
