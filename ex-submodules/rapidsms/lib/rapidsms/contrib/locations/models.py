from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.html import escape
import uuid

from logistics.mixin import StockCacheMixin


class Point(models.Model):
    """
    This model represents an anonymous point on the globe. It should be
    replaced with something from GeoDjango soon, but I can't seem to get
    Spatialite to build right now...
    """

    latitude = models.DecimalField(max_digits=13, decimal_places=10)
    longitude = models.DecimalField(max_digits=13, decimal_places=10)

    def __unicode__(self):
        return "%s, %s" % (self.latitude, self.longitude)

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)

class LocationType(models.Model):
    """
    This model represents the 'type' of Location, as an option for a
    simpler way of having a location heirarchy without having different
    classes for each location type (as is supported by the generic 
    relation to parent).  
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, primary_key=True)

    def __unicode__(self):
        return self.name

class LocationManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Location(models.Model, StockCacheMixin):
    """
    This model represents a named point on the globe. It is deliberately
    spartan, so more specific apps can extend it with their own fields
    and relationships without clashing with built-in functionality.
    """

    objects = LocationManager()
    point = models.ForeignKey(Point, on_delete=models.CASCADE,  null=True, blank=True)

    type = models.ForeignKey(LocationType, on_delete=models.CASCADE,  related_name="locations", blank=True, null=True)
    parent_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,  null=True, blank=True)
    parent_id = models.PositiveIntegerField(null=True, blank=True)
    parent = GenericForeignKey("parent_type", "parent_id")

    code = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    # choices for the Location.direction method.
    # (values stolen from label-overlay.js)
    class Direction:
        CENTER = "center"
        ABOVE = "above"
        RIGHT = "right"
        BELOW = "below"
        LEFT = "left"

    def __unicode__(self):
        """
        """
        
        return getattr(self, "name", "#%d" % self.pk if self.pk else "unsaved facility")

    @property
    def uid(self):
        """
        Return a unique ID for this location, suitable for embedding in
        URLs. The primary key is insufficient, because the name of the
        model must also be included.

        This method (and ``get_for_uid`` will go away, once the ``slug``
        field is validated as unique across all Location subclasses.
        """

        return "%s:%d" % (self.content_type, self.pk)

    @property
    def content_type(self):
        return ContentType.objects.get_for_model(self).model

    @staticmethod
    def get_for_uid(uid):
        """
        Return the object (an instance of a subclass of Location) named
        by ``uid``. The UID should be in the form ``model:id``, as
        returned by the Location.uid property.
        """

        model, pk = uid.split(":")
        type = ContentType.objects.get(model=model)
        return type.get_object_for_this_type(pk=pk)

    @property
    def path(self):
        next = self
        locations = []

        while next is not None:
            locations.insert(0, next)
            next = next.parent

        return locations

    def as_html(self):
        """
        Return the HTML fragment to be embedded in the map. This method
        should be overridden by subclasses wishing to fully customize
        the the rendering of their instance in the map.

        The output of this method is not escaped before being included
        in the template, so be careful to escape it yourself.
        """

        return escape(self.label)

    @property
    def label(self):
        """
        Return the caption for this Location, to be embedded in the
        map. This method should be overridden by subclasses wishing to
        provide better contextual information.

        The output of this method is included in the template as-is, so
        is HTML-escaped by default. If you wish to customize the HTML,
        override the ``as_html`` method, instead.
        """

        return unicode(self)

    @property
    def css_class(self):
        """
        Return the CSS class name of the label overlay. This method
        should be overriden by subclasses wishing to customize the
        appearance of the embedded HTML fragment.
        """

        return "bubble"

    @property
    def direction(self):
        """
        Return the direction which the embedded HTML fragment should be
        offset from the anchor point. Return one of Location.Direction.
        """

        return self.Direction.ABOVE

    # logistics extensions
    def set_parent(self, parent):
        if hasattr(self,'tree_parent'):
            self.tree_parent = parent
        else:
            self.parent = parent
        self.save()

    def is_any_parent(self, location):
        """
        Returns true of this is any parent of the location or its
        entire parent chain.
        """
        # no infinite loops pls
        seen_locs = []
        while location and location.parent and location not in seen_locs:
            if self == location.parent:
                return True
            seen_locs.append(location)
            location = location.parent
        return False

    @property
    def tree_parent(self):
        """ This signature gets overriden by mptt when mptt is used """
        return self.parent

    @tree_parent.setter
    def tree_parent(self, value):
        """ This signature gets overriden by mptt when mptt is used """
        self.parent = value

    def get_children(self):
        """ This signature gets overriden by mptt when mptt is used """
        from rapidsms.contrib.locations.models import Location
        return Location.objects.filter(parent_id=self.id, is_active=True).order_by('name')

    def get_descendants(self, include_self=False):
        """ This signature gets overriden by mptt when mptt is used
        It must return a queryset
        """
        def _get_descendent_pks(node):
            pks = []
            for c in node.get_children():
                pks.append(c.pk)
                pks.extend(_get_descendent_pks(c))
            return pks
        pks = _get_descendent_pks(self)
        if include_self:
            pks.append(self.pk)
        ret = Location.objects.filter(id__in=pks, is_active=True)
        return ret

    def get_descendants_plus_self(self):
        # utility to facilitate calling function from django template
        return self.get_descendants(include_self=True)

    def child_facilities(self):
        from logistics.models import SupplyPoint
        return SupplyPoint.objects.filter(Q(location=self)|Q(location__parent_id=self.pk), active=True).order_by('name')

    def facilities(self):
        from logistics.models import SupplyPoint
        return SupplyPoint.objects.filter(location=self, active=True).order_by('name')

    def all_facilities(self):
        from logistics.models import SupplyPoint
        locations = self.get_descendants(include_self=True)
        return SupplyPoint.objects.filter(location__in=locations, active=True).order_by('name')

    def all_child_facilities(self):
        from logistics.models import SupplyPoint
        locations = self.get_descendants()
        return SupplyPoint.objects.filter(location__in=locations, active=True).order_by('name')

    def _cache_key(self, key, product, producttype, datetime=None):
        return ("LOC-%(location)s-%(key)s-%(product)s-%(producttype)s-%(datetime)s" % \
                {"key": key, "location": self.code, "product": product,
                 "producttype": producttype, "datetime": datetime}).replace(" ", "-")

    def _get_stock_count(self, operation, product, producttype, datespan=None):
        """
        pulls requested value from cache. refresh cache if necessary
        """
        return self._get_stock_count_for_facilities(self.all_facilities(), operation,
                                                    product, producttype, datespan)

    """ The following methods express AGGREGATE counts, of all subsumed facilities"""
    def stockout_count(self, product=None, producttype=None, datespan=None):
        return self._get_stock_count("stockout_count", product, producttype, datespan)

    def emergency_stock_count(self, product=None, producttype=None, datespan=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("emergency_stock_count", product, producttype, datespan)

    def low_stock_count(self, product=None, producttype=None, datespan=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("low_stock_count", product, producttype, datespan)

    def emergency_plus_low(self, product=None, producttype=None, datespan=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("emergency_plus_low", product, producttype, datespan)

    def good_supply_count(self, product=None, producttype=None, datespan=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("good_supply_count", product, producttype, datespan)

    def overstocked_count(self, product=None, producttype=None, datespan=None):
        return self._get_stock_count("overstocked_count", product, producttype, datespan)

    def other_count(self, product=None, producttype=None, datespan=None):
        return self._get_stock_count("other_count", product, producttype, datespan)

    def consumption(self, product=None, producttype=None):
        return self._get_stock_count("consumption", product, producttype)

    def deprecate(self, new_code=None):
        """
        Deprecates a location, by changing the code and deactivating it.
        """
        if new_code is None:
            new_code = "deprecated-%s-%s" % (self.code, uuid.uuid4())
        self.code = new_code
        self.is_active = False
        self.save()
