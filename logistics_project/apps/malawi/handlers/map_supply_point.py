from __future__ import unicode_literals
from builtins import str
from django.utils.translation import gettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.util import config
from logistics.models import SupplyPoint
from rapidsms.contrib.locations.models import Location, Point
import logging

logger = logging.getLogger("django")


class MapSupplyPointHandler(KeywordHandler):
    """
    Set the location of a supply point using "map"
    """

    keyword = "map"

    def help(self):
        self.respond(config.Messages.MAP_HELP)

    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact') or \
           not self.msg.logistics_contact.is_active:
            self.respond(_(config.Messages.NOT_REGISTERED))
        else:
            # self.msg.logistics_contact.is_active = False
            # self.msg.logistics_contact.commodities.clear()
            # self.msg.logistics_contact.save()
            # if self.msg.logistics_contact.supply_point and \
            #    self.msg.logistics_contact.supply_point.type == config.hsa_supply_point_type():
            #     self.msg.logistics_contact.supply_point.deprecate()

            words = text.split()
            if len(words) < 2:
                self.help()
            else:
                latitude = words[0]
                longitude = words[1]

                if(self._validate_latitude(latitude) and self._validate_longitude(longitude)):
                    # create location record and link to supply point
                    
                    logger.info("Mapping location")
                    point = Point(latitude=float(latitude), longitude=float(longitude))
                    point.save()
                    self.msg.connection.contact.supply_point.location.point = point
                    self.msg.connection.contact.supply_point.location.save()
                    
                    self.respond(_(config.Messages.MAP_SUCCESS), sp_name=self.msg.connection.contact.supply_point)
                else:
                    logger.info(config.Messages.INVALID_COORDINATES)
                    self.respond(_(config.Messages.INVALID_COORDINATES))

            # try:
            #     self.supply_point = SupplyPoint.objects.get(active=True, code__iexact=code)
            # except SupplyPoint.DoesNotExist:
            #     self.respond(_(config.Messages.UNKNOWN_LOCATION), code=code)
            # self.respond(_(config.Messages.MAP_SUCCESS),
            #              sp_name=self.supply_point.name)

    def _validate_latitude(self,latitude):
        if self._is_float(latitude):
            lat_value = float(latitude)
            if (lat_value > -90) and (lat_value < 90):
                return True
            else:
                return False
        else:
            return False

    def _validate_longitude(self,longitude):
        if self._is_float(longitude):
            long_value = float(longitude)
            if (long_value > -180) and (long_value < 180):
                return True
            else:
                return False
        else:
            return False

    def _is_float(self,string):
        try:
            float(string)
            return True
        except ValueError:
            return False
