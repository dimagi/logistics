from __future__ import unicode_literals
from django.test import SimpleTestCase
from ..log.mixin import LoggerMixin


class LoggableStub(LoggerMixin):
    pass


class LoggerTest(SimpleTestCase):
    
    def test_logger_mixin(self):
        obj = LoggableStub()
    
        from logging.handlers import MemoryHandler
        import logging
    
        log = logging.getLogger()
        handler = MemoryHandler(999)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
    
        obj.debug("This is a DEBUG message")
        obj.info("This is an INFORMATIVE message")
        obj.warning("This is a WARNING")
        obj.error("This is an ERROR")
        obj.critical("This is a CRITICAL error")
        obj.exception("This is an exception")
        obj.exception()
    
        self.assertEqual(len(handler.buffer), 7)
        self.assertEqual(handler.buffer[2].name, "loggablestub")
        self.assertEqual(handler.buffer[2].msg, "This is a WARNING")
    
        log.removeHandler(handler)

    def test_logger_raises_on_invalid_name_type(self):
        class BrokenLoggableStub(LoggerMixin):
            def _logger_name(self):
                return 123
    
        broken_logger = BrokenLoggableStub()
    
        with self.assertRaises(TypeError):
            broken_logger.debug("This shouldn't work")
