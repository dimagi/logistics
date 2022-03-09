from collections import OrderedDict

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.decorators import logistics_contact_required
from logistics.models import Product
from logistics.util import config


class Help(KeywordHandler):
    keyword = "help"

    @logistics_contact_required()
    def help(self):
        self.respond(config.Messages.HELP_TEXT)

    @logistics_contact_required()
    def handle(self, text):
        is_hsa = (
            self.msg.logistics_contact.supply_point and
            self.msg.logistics_contact.supply_point.type_id == config.SupplyPointCodes.HSA
        )
        topic = text.strip().lower()

        if topic == 'stock':
            self.respond(config.Messages.SOH_HELP_MESSAGE)
        elif 'code' in topic:
            products = Product.objects.filter(is_active=True).select_related('type').order_by("type__id", "sms_code")

            # Only show HSA-level products to HSAs; show all products to everyone else
            if is_hsa:
                products = products.filter(type__base_level=config.BaseLevel.HSA)

            grouped_codes = OrderedDict()
            for p in products:
                if p.type.name not in grouped_codes:
                    grouped_codes[p.type.name] = []
                grouped_codes[p.type.name].append(p.sms_code.lower())

            messages = []
            for type_name, codes in grouped_codes.iteritems():
                messages.append("%s codes: %s" % (type_name, " ".join(codes)))

            self.respond("; ".join(messages))
        else:
            try:
                if is_hsa:
                    p = Product.objects.get(sms_code=topic, is_active=True, type__base_level=config.BaseLevel.HSA)
                else:
                    p = Product.objects.get(sms_code=topic, is_active=True)
            except Product.DoesNotExist:
                self.respond(config.Messages.HELP_TEXT)

            msg = "%s is the code for %s product %s" % (topic, p.type.name, p.name)
            if p.units:
                msg = msg + " (%s)" % p.units

            self.respond(msg)
