from rapidsms.conf import settings
from django.core.cache import cache
from django.db.models import Sum

class StockCacheMixin():
    """
    This mixin provides a consistent set of stock parameters which can be calculated
    and cached using class-specific methods. It is useful for reusing similar code
    (such as stockount_count() and overstock_count()) across very different models
    (such as facility, location, group, etc.)
    """

    def _populate_stock_cache(self, facilities, product, producttype, datespan=None):
        """ 
        refreshes all the stock count values in the cache in bulk
        returns None
        """
        stocks = self._filtered_stock(product, producttype)\
                  .filter(supply_point__in=facilities)
        # TODO: when datespan is None, stockouts can be queried more efficiently 
        # at the db level. 
        #nonzero_stocks = all_stocks.filter(quantity__gt=0)
        stockout_count = 0
        emergency_stock_count = 0
        low_stock_count = 0
        emergency_plus_low = 0
        good_supply_count = 0
        adequate_supply_count = 0
        overstocked_count = 0    
        for stock in stocks:
            #if datespan:
            #    historical_stock = stock.supply_point.historical_stock_by_date(stock.product, datespan.end_of_end_day)
            #    stock.quantity = historical_stock
            if stock.quantity == 0:
                stockout_count = stockout_count + 1
            if stock.is_below_emergency_level():
                emergency_stock_count = emergency_stock_count + 1
            if stock.is_below_low_supply_but_above_emergency_level():
                low_stock_count = low_stock_count + 1
            if stock.is_below_low_supply():
                emergency_plus_low = emergency_plus_low + 1
            if stock.is_in_good_supply():
                good_supply_count = good_supply_count + 1
            if stock.is_in_adequate_supply():
                adequate_supply_count = adequate_supply_count + 1
            if stock.is_overstocked():
                overstocked_count = overstocked_count + 1
        cache.set(self._cache_key('stockout_count', product, producttype, datespan), 
                  stockout_count, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)       
        cache.set(self._cache_key('emergency_stock_count', product, producttype, datespan), 
                  emergency_stock_count, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)       
        cache.set(self._cache_key('low_stock_count', product, producttype, datespan), 
                  low_stock_count, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)       
        cache.set(self._cache_key('emergency_plus_low', product, producttype, datespan), 
                  emergency_plus_low, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)       
        cache.set(self._cache_key('good_supply_count', product, producttype, datespan), 
                  good_supply_count, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)       
        cache.set(self._cache_key('adequate_supply_count', product, producttype, datespan), 
                  adequate_supply_count, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)       
        cache.set(self._cache_key('overstocked_count', product, producttype, datespan), 
                  overstocked_count, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)
        consumption = stocks.exclude(manual_monthly_consumption=None).aggregate(consumption=Sum('manual_monthly_consumption'))['consumption']
        # NB: we do not yet support historical consumption, 
        # since that's its own giant bag of worms
        cache.set(self._cache_key('consumption', product, producttype, datespan), 
                  consumption, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)
    
    def _get_stock_count_for_facilities(self, facilities, name, product, producttype, datespan=None):
        """ 
        pulls requested stock value for a given set of facilities from the cache
        refresh cache if necessary
        returns integer
        """
        #TEMPORARY
        self._populate_stock_cache(facilities, product, producttype, datespan)
        if settings.LOGISTICS_USE_SPOT_CACHING:
            from_cache = cache.get(self._cache_key(name, product, producttype, datespan))
            if from_cache:
                return from_cache
        # if LOGISTICS_USE_SPOT_CACHING is not enabled, we refresh the cache each time
        self._populate_stock_cache(facilities, product, producttype, datespan)
        return cache.get(self._cache_key(name, product, producttype, datespan))

    def _filtered_stock(self, product, producttype):
        """ 
        returns a QuerySet of ProductStock filetered by product and product type
        """
        from logistics.models import ProductStock
        results = ProductStock.objects.filter(is_active=True)
        if product is not None:
            results = results.filter(product__sms_code=product)
        elif producttype is not None:
            results = results.filter(product__type__code=producttype)
        return results
