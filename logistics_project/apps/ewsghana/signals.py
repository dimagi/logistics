#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from logistics.signals import stockout_resolved, notify_suppliees_of_stockouts_resolved
from logistics.signals import stockout_reported, notify_suppliees_of_stockouts_reported

stockout_resolved.connect(notify_suppliees_of_stockouts_resolved)
stockout_reported.connect(notify_suppliees_of_stockouts_reported)
