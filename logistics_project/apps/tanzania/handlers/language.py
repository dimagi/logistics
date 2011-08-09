from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.conf import settings
from logistics.util import config


class LanguageHandler(KeywordHandler):
    """
    Allow remote users to set their preferred language, by updating the
    ``language`` field of the Contact associated with their connection.
    """

    keyword = "language|lang|lugha"

    def help(self):
        self.respond(config.Messages.LANGUAGE_HELP)

    def handle(self, text):
        if self.msg.connection.contact is None:
            return self.respond_error(config.Messages.LANGUAGE_CONTACT_REQUIRED)

        t = text.lower()
        for code, name in settings.LANGUAGES:
            if t != code.lower() and t != name.lower():
                continue

            self.msg.connection.contact.language = code
            self.msg.connection.contact.save()

            return self.respond(config.Messages.LANGUAGE_CONFIRM,
                                language=name)

        return self.respond_error(config.Messages.LANGUAGE_UNKNOWN, 
                                  language=text)