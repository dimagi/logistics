from .base import BaseHandler

"""
This handler tags messages as they are responded to.
Messages are automatically tagged if the respond() or
respond_error() methods are called, but if those methods
are not used, messages can still be tagged using the
add_tag() or add_tags() methods.
"""
class TaggingHandler(BaseHandler):
    
    """
      This method is just like BaseHandler.respond, only it
    adds default tags (see add_default_tags()) and allows
    for application-specific tagging.
      To add application-specific tags, send them as a list 
    of strings in the "tags" keyword argument (e.g., 
    tags=["FirstResponse","FirstTimeUser"], etc.)
    """
    def respond(self, template=None, **kwargs):
        self.add_default_tags()
        self.add_tags(kwargs.get("tags", []))
        return self.msg.respond(template, **kwargs)
    
    """
      This method is just like BaseHandler.respond_error, only it
    adds default tags (see add_default_tags()), adds and "Error" 
    tag, and allows for application-specific tagging.
      To add application-specific tags, send them as a list 
    of strings in the "tags" keyword argument (e.g., 
    tags=["FirstResponse","FirstTimeUser"], etc.)
    """
    def respond_error(self, template=None, **kwargs):
        self.add_default_tags()
        self.add_tags(kwargs.get("tags", []))
        self.add_tag("Error")
        return self.msg.error(template, **kwargs)
    
    """
    Tags the current message with the given string.
    """
    def add_tag(self, tag):
        self.msg.logger_msg.tags.add(tag)
    
    """
    Tags the current message with each string in the given list.
    """
    def add_tags(self, tags):
        for tag in tags:
            self.add_tag(tag)
    
    """
    Adds the following tags to the current message:
        "Handler_" + <name of current handler class>
        "RegisteredContact" if the message came from a contact in the database
        "UnregisteredContact" if the message did not come from a contact in the database
    """
    def add_default_tags(self):
        self.add_tag("Handler_" + self.__class__.__name__)
        if self.msg.connection.contact:
            self.add_tag("RegisteredContact")
        else:
            self.add_tag("UnregisteredContact")

