from __future__ import absolute_import
from datetime import date, timedelta
from django.db import models


class TanzaniaSupplyPointExtension(models.Model):
    is_pilot = models.BooleanField(default=False)
    closest_supply_points = models.ManyToManyField('self', related_name='closest', symmetrical=True,
                                                   limit_choices_to={'is_pilot': True}, null=False, blank=True)

    class Meta:
        abstract = True

    def overstocked_products(self):
        return self._facility_products_with_state()

    def stockout_products(self):
        result = {}
        for k, v in self._facility_products_with_state(state='stockout').iteritems():
            result[k] = v[0]
        return result

    def _facility_products_with_state(self, state='overstocked'):
        from logistics.models import ProductStock
        from logistics.models import ProductReport

        if state == 'overstocked':
            cond = lambda (x): x > 6
        elif state == 'stockout':
            cond = lambda (x): x < 0.35
        else:
            return {}

        if self.type.name != 'FACILITY':
            return {}
        product_stocks = ProductStock.objects.filter(supply_point=self).only('supply_point', 'product',
                                                                             'auto_monthly_consumption')
        stock_level = {}
        last_ten_days = date.today() - timedelta(days=10)
        for product_stock in product_stocks:
            try:
                report = ProductReport.objects.filter(supply_point=self,
                                                      product=product_stock.product,
                                                      report_type_id=1,
                                                      report_date__gte=last_ten_days).latest('report_date')
                if not product_stock.auto_monthly_consumption or product_stock.auto_monthly_consumption == 0:
                    if report.quantity == 0:
                        remaining = 0
                    else:
                        continue
                else:
                    remaining = report.quantity / float(product_stock.auto_monthly_consumption)

                if cond(remaining):
                    stock_level[product_stock.product.sms_code] = (report.quantity, report.quantity -
                                                                   6 * product_stock.auto_monthly_consumption)
            except ProductReport.DoesNotExist:
                continue

        return stock_level