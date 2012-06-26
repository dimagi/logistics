from __future__ import absolute_import
from django.db import models
from rapidsms.conf import settings

class Contact(models.Model):
    """ 
    Note: this model extension assumes that we have only one connection
    per SMS user, so if we re-assign the 'default connection', we delete
    the unused connection after reassignment
    """

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

    @property
    def default_connection(self):
        """
        Return the default connection for this person.
        """
        # TODO: this is defined totally arbitrarily for a future 
        # sane implementation
        if self.connection_set.count() > 0:
            return self.connection_set.all()[0]
        return None

    @default_connection.setter
    def default_connection(self, identity):
        from rapidsms.models import Connection
        backend = self.default_backend
        default = self.default_connection
        if default is not None:
            if default.identity == identity and default.backend == backend:
                # our job is done
                return
            # when you re-assign default connection, 
            # should you delete the unused connection? 
            # probably not because who knows what else will get deleted in the
            # cascade
            # default.delete()
        try:
            conn = Connection.objects.get(backend=backend, identity=identity)
        except Connection.DoesNotExist:
            # good, it doesn't exist already
            conn = Connection(backend=backend,
                              identity=identity)
        conn.contact = self
        conn.save()
