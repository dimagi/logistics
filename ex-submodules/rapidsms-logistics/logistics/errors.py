#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


class UnknownCommodityCodeError(ValueError):

    def __init__(self, product_code, *args, **kwargs):
        self.product_code = product_code
        super(UnknownCommodityCodeError, self).__init__(product_code, *args, **kwargs)


class UnknownFacilityCodeError(ValueError):
    pass


class UnknownLocationCodeError(ValueError):
    pass
