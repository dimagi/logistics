from django import template
from logistics.util import config
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from logistics.models import Product
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def product_inventory(facility, view_type):
    return render_to_string("tanzania/partials/product_inventory.html", 
                              {"view_type": view_type,
                               "product_stocks": facility.product_stocks().all()})
