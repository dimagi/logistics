from __future__ import unicode_literals
from django.db import models
from django.core.exceptions import ValidationError
from rapidsms.models import Contact, Connection
from taggit.managers import TaggableManager


DIRECTION_CHOICES = (
    ("I", "Incoming"),
    ("O", "Outgoing"))


class Message(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE,  null=True)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE,  null=True)
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    date = models.DateTimeField()
    text = models.TextField()
    tags = TaggableManager()

    def save(self, *args, **kwargs):
        """
        Verifies that one (not both) of the contact or connection fields
        have been populated (raising ValidationError if not), and saves
        the object as usual.
        """

        if (self.contact or self.connection) is None:
            raise ValidationError(
                "A valid (not null) contact or connection (but "
                "not both) must be provided to save the object")

        elif (self.connection and self.contact and \
              self.contact!= self.connection.contact):

            raise ValidationError(
                "The connection and contact you tried to save "  
                "did not match! You need to pick one or the other.")

        elif self.connection is not None and \
             self.connection.contact is not None:
            # set the contact here as well, even if they didn't
            # do it explicitly.  If the contact's number changes
            # we still might want to know who it originally came
            # in from.  
            self.contact = self.connection.contact
        
        # all is well; save the object as usual
        models.Model.save(self, *args, **kwargs)

    @property
    def who(self):
        """Returns the Contact or Connection linked to this object."""
        return self.contact or self.connection

    def __str__(self):

        # crop the text (to avoid exploding the admin)
        if len(self.text) < 60: str = self.text
        else: str = "%s..." % (self.text[0:57])

        to_from = (self.direction == "I") and "from" or "to"
        return "%s (%s %s)" % (str, to_from, self.who)
    
    """
    Returns a string showing all tags for this Message,
    separated by a comma. If this Message does not have any
    tags, an empty string is returned.
    """
    def get_tags_for_display(self):
        tag_list = []
        for tag in self.tags.all():
            tag_list.append(tag.name)
        tag_list.sort()
        
        display = ""
        if len(tag_list) > 0:
            display = ", ".join(tag_list)
        
        return display

