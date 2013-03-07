#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.decorators import logistics_contact_required, \
    logistics_supply_point_required
from logistics.models import ProductReport, StockTransaction, \
    ProductStock

class UndoHandler(KeywordHandler):
    """
    Undo previous stock report
    """

    keyword = "undo|replace|revoke"

    def help(self):
        return self.handle(self.msg.text)

    @logistics_contact_required()
    @logistics_supply_point_required()
    def handle(self, text):
        # get the last product report (for  single product)
        all_prs = ProductReport.objects.filter(message__contact=\
                                               self.msg.logistics_contact)\
                                       .order_by("-report_date")
        if not all_prs:
            return self.respond("You have not submitted any product reports yet.")
        last_productreport_message = all_prs[0].message
        sp = all_prs[0].supply_point
        # get all the product reports associated with the last product report message
        prs = ProductReport.objects.filter(message=last_productreport_message)\
                                   .order_by('-report_date')
        sts = StockTransaction.objects.filter(product_report__in=prs)
        # 1. undo the stock information at the given facility """
        for st in sts:
            product_stock = ProductStock.objects.get(supply_point=sp, 
                                                     product=st.product)
            product_stock.quantity = st.beginning_balance
            product_stock.save()
            # 2 delete the stock transaction
            st.delete()
        # 3 delete the product report
        for pr in prs:
            pr.delete()
        # 4 update auto consumption values
        product_stocks = ProductStock.objects.filter(supply_point=sp)
        for ps in product_stocks:
            ps.update_auto_consumption()
        return self.respond(
            "Success. Your previous report has been removed. It was: %(report)s",
            report=last_productreport_message.text)
