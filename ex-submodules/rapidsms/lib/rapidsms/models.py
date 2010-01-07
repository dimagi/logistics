#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models
from django.db.models.base import ModelBase
from .utils.modules import find_extensions


class Extensible(ModelBase):
    """
    """

    def __new__(cls, name, bases, attrs):

        module_name = attrs["__module__"]
        app_label = module_name.split('.')[-2]
        model_name = "%s.%s" % (app_label, name)

        extensions = find_extensions(model_name)
        bases = tuple(extensions) + bases

        return super(Extensible, cls).__new__(
            cls, name, bases, attrs)


def extends(name):
    def wrapped(func):
        func._extends = name
        return func

    return wrapped


class Backend(models.Model):
    """
    This model isn't really a backend. Those are regular Python classes,
    in rapidsms/backends. This is just a stub model to provide a primary
    key for each running backend, so other models can be linked to it
    with ForeignKeys.
    """

    name = models.CharField(max_length=20, unique=True)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)


class App(models.Model):
    """
    This model isn't really a RapidSMS App. Like Backend, it's just a
    stub model to provide a primary key for each app, so other models
    can be linked to it.

    The Django ContentType stuff doesn't quite work here, since not all
    RapidSMS apps are valid Django apps. It would be nice to fill in the
    gaps and inherit from it at some point in the future.

    Instances of this model are generated by the update_apps management
    command, (which is hooked on Router startup (TODO: webui startup)),
    and probably shouldn't be messed with after that.
    """

    module = models.CharField(max_length=100, unique=True)
    active = models.BooleanField()

    def __unicode__(self):
        return self.module

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)


class Connection(models.Model):
    """
    This model pairs a Backend object with an identity unique to it (eg.
    a phone number, email address, or IRC nick), so RapidSMS developers
    need not worry about which backend a messge originated from.
    """

    __metaclass__ = Extensible

    backend  = models.ForeignKey(Backend)
    identity = models.CharField(max_length=100)

    def __unicode__(self):
        return "%s via %s" %\
            (self.identity, self.backend)

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)


class Contact(models.Model):
    """
    """

    __metaclass__ = Extensible

    connections = models.ManyToManyField(Connection, blank=True)

    alias = models.CharField(max_length=20, blank=True)
    name  = models.CharField(max_length=100, blank=True)

    # the language that this person prefers to communicate in, as a w3c
    # language tag. if this field is blank (or invalid), rapidsms will
    # default to settings.LANGUAGE_CODE.
    #
    # the spec: http://www.w3.org/International/articles/language-tags/Overview
    # reference:http://www.iana.org/assignments/language-subtag-registry
    #
    # for example:
    #   english  = en
    #   amharic  = am
    #   chichewa = ny
    #   klingon  = tlh
    language = models.CharField(max_length=4, blank=True)

    def __unicode__(self):
        return self.alias

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)
