from __future__ import absolute_import
from __future__ import unicode_literals
from logistics.errors import UnknownCommodityCodeError
from logistics.exceptions import TooMuchStockError
from logistics.models import ProductStock
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from static.malawi.config import BaseLevel


def check_max_levels_malawi(stock_report):
    """
    checks a stock report against maximum allowable levels. if more than the
    allowable threshold of stock is being reported it throws a validation error
    """
    hard_coded_max_thresholds = {
        "ab": 200,
        "am": 1000,
        "cl": 300,
        "cf": 1000,
        "cm": 5000,
        "co": 2000,
        "cw": 1000,
        "de": 300,
        "dm": 300,
        "gl": 1000,
        "la": 2000,
        "lb": 2000,
        "lc": 300,
        "mb": 300,
        "mt": 1000,
        "or": 500,
        "pa": 2000,
        "pb": 2000,
        "po": 500,
        "ra": 100,
        "ss": 100,
        "te": 100,
        "un": 100,
        "zi": 2000,
        "bc": 15000,
        "op": 27000,
        "ip": 6000,
        "pe": 21000,
        "pn": 21000,
        "ro": 15000,
        "ru": 500,
        "me": 18000,
        "tv": 24000,
        "sa": 10000,
        "sb": 10000,
        "sc": 10000,
        "sd": 10000,
        "sf": 1000,
        "syna": 500,
    }
    MAX_REPORT_LEVEL_FACTOR = 6

    def _over_static_threshold(product_code, stock):
        return (
            not product_code or   # unknown, consider over
            product_code.lower() not in hard_coded_max_thresholds or  # not found, consider over
            stock > hard_coded_max_thresholds[product_code.lower()]  # actually over
        )
    for product_code, stock in list(stock_report.product_stock.items()):
        if _over_static_threshold(product_code, stock):
            product = stock_report.get_product(product_code)
            try:
                current_stock = ProductStock.objects.get(supply_point=stock_report.supply_point,
                                                         product=product)
                if current_stock.maximum_level:
                    max_allowed = current_stock.maximum_level * MAX_REPORT_LEVEL_FACTOR
                    if stock > max_allowed:
                        raise TooMuchStockError(product=product, amount=stock, max=max_allowed)

            except ProductStock.DoesNotExist:
                pass


def _require_products_base_level(stock_report, base_level):
    invalid_products = []
    for product_code in stock_report.product_stock:
        product = stock_report.get_product(product_code)
        if product.type.base_level != base_level:
            invalid_products.append(product_code)

    for error in stock_report.errors:
        if isinstance(error, UnknownCommodityCodeError):
            invalid_products.append(error.product_code)

    if invalid_products:
        raise BaseLevel.InvalidProductsException(invalid_products)


def require_hsa_level_products(stock_report):
    _require_products_base_level(stock_report, BaseLevel.HSA)


def require_facility_level_products(stock_report):
    _require_products_base_level(stock_report, BaseLevel.FACILITY)


def require_working_refrigerator(stock_report):
    if RefrigeratorMalfunction.get_open_malfunction(stock_report.supply_point):
        raise RefrigeratorMalfunction.RefrigeratorNotWorkingException()


def get_base_level_validator(base_level):
    if base_level == BaseLevel.HSA:
        return require_hsa_level_products
    elif base_level == BaseLevel.FACILITY:
        return require_facility_level_products
    else:
        raise BaseLevel.InvalidBaseLevelException(base_level)


def combine_validators(validators):
    def final_validator(stock_report):
        for validator in validators:
            validator(stock_report)
    return final_validator
