from __future__ import absolute_import
from django.db import models
from rapidsms.conf import settings

class Contact(models.Model):
    class Meta:
        abstract = True

    @property
    def default_backend(self):
        from rapidsms.models import Backend
        # TODO: this is defined totally arbitrarily for a future 
        # sane implementation
        if settings.DEFAULT_BACKEND:
            return Backend.objects.get(name=settings.DEFAULT_BACKEND)
        else:
            return Backend.objects.all()[0]
    
    def get_other_connections(self):
        from rapidsms.models import Connection
        conns = Connection.objects.filter(contact=self)
        if self.default_connection:
            conns = conns.exclude(pk__in=[self.default_connection.pk])
        return conns

    def add_phone_number(self, identity):
        """ create or steal the connection as needed """
        from rapidsms.models import Connection
        backend = self.default_backend
        try:
            conn = Connection.objects.get(backend=backend, identity=identity)
        except Connection.DoesNotExist:
            conn = Connection(backend=backend,
                              identity=identity)
        conn.contact = self
        conn.save()
