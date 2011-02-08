#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import logging
from re import match
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Max
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from rapidsms.models import ExtensibleModelBase
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact as RapidSMSContact
from rapidsms.models import Connection
from rapidsms.contrib.messagelog.models import Message

class ServiceDeliveryPointType(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class ServiceDeliveryPoint(Location):
    """
    ServiceDeliveryPoint - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.
    This could/should be broken out into subclasses.
    """
    @property
    def label(self):
        return unicode(self)

    name = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    msd_code = models.CharField(max_length=100, blank=True, null=True)
    service_delivery_point_type = models.ForeignKey(ServiceDeliveryPointType)

class Product(models.Model):
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=100)
    sms_code = models.CharField(max_length=10)
    description = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100, null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
class ProductInStock(models.Model):
    is_active = models.BooleanField(default=True)
    quantity = models.IntegerField(blank=True, null=True)
    service_delivery_point = models.ForeignKey('ServiceDeliveryPoint')
    product = models.ForeignKey('Product')

class Responsibility(models.Model):
    slug = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Responsibility"
        verbose_name_plural = "Responsibilities"

    def __unicode__(self):
        return _(self.name)

class ContactRole(models.Model):
    slug = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=100, blank=True)
    responsibilities = models.ManyToManyField(Responsibility, blank=True, null=True)

    class Meta:
        verbose_name = "Role"

    def __unicode__(self):
        return _(self.name)
    
class LogisticsContact(RapidSMSContact):
    role = models.ForeignKey(ContactRole, null=True, blank=True)
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint,null=True,blank=True)

    class Meta:
        verbose_name = "Contact Detail"

    def __unicode__(self):
        return self.name

    @property
    def phone(self):
        if self.default_connection:
            return self.default_connection.identity
        else:
            return " "


