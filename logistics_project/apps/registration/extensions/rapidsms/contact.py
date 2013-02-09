from __future__ import absolute_import
from django.db import models
from rapidsms.conf import settings

class Contact(models.Model):
    """ 
    Note: this model extension assumes that we have only one connection
    per SMS user, so if we re-assign the 'default connection', we delete
    the unused connection after reassignment
    """
    _default_connection  = models.ForeignKey('Connection', null=True, 
                                             blank=True, 
                                             related_name='contact+', 
                                             on_delete=models.SET_NULL)

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

    @property
    def default_connection(self):
        """
        Return the default connection for this person.
        """
        # TODO: this is defined totally arbitrarily for a future 
        # sane implementation
        if self._default_connection:
            return self._default_connection
        if self.connection_set.count() > 0:
            return self.connection_set.all()[0]
        return None

    @default_connection.setter
    def default_connection(self, identity):
        # when you re-assign default connection, should you delete the unused connection? probably.
        from rapidsms.models import Connection
        backend = self.default_backend
        default = self.default_connection
        if default is not None:
            if default.identity == identity and default.backend == backend:
                # our job is done
                return
            default.delete()
        try:
            conn = Connection.objects.get(backend=backend, identity=identity)
        except Connection.DoesNotExist:
            # good, it doesn't exist already
            conn = Connection(backend=backend,
                              identity=identity)
        conn.contact = self
        conn.save()
        self._default_connection = conn
        self.save()
