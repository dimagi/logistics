from django.test import TestCase
import time
import threading
from ...backends.base import BackendBase


class BackendStub(BackendBase):
    pass


class BackendBaseTest(TestCase):
    
    def test_backend_has_name(self):
        backend = BackendStub(None, "mock")
    
        self.assertEqual(repr(backend), "<backend: mock>")
        self.assertEqual(unicode(backend), "mock")
        self.assertEqual(backend.name, "mock")
    
    
    def test_backend_has_model(self):
        backend = BackendStub(None, "mock")
        from ...models import Backend as B
    
        # before fetching the model via BackendBase, check that it does not
        # already exist in the db. (if it does, this test checks nothing.)
        self.assertEqual(B.objects.filter(name="mock").count(), 0)
    
        # the row should be created when .model is called.
        self.assertEqual(backend.model.__class__, B)
        self.assertEqual(backend.model.name, "mock")
    
        # check that the backend stub was committed to the db.
        self.assertEqual(B.objects.filter(name="mock").count(), 1)
    
        # tidy up the db.
        B.objects.filter(name="mock").delete()

    def test_backend_creates_connections(self):
        backend = BackendStub(None, "mock")
        from ...models import Connection as C
    
        # check that the mock connection doesn't already exist.
        self.assertEqual(C.objects.filter(identity="mock").count(), 0)
    
        msg = backend.message("mock", "Mock Message")
    
        self.assertEqual(msg.text, "Mock Message")
        self.assertEqual(msg.connection.identity, "+mock")
        self.assertEqual(msg.connection.backend, backend.model)

        # check that the connection was committed to the db.
        self.assertEqual(C.objects.filter(identity="+mock").count(), 1)
    
        # tidy up the db.
        C.objects.filter(identity="+mock").delete()

    def test_backend_passes_kwargs_to_configure(self):
        class ConfigurableBackend(BackendBase):
            def configure(self, **kwargs):
                self.conf = kwargs
    
        conf_backend = ConfigurableBackend(None, "mock", a=1, b=2)
        self.assertEqual(conf_backend.conf, {"a": 1, "b": 2 })
    
    
    def test_backend_routes_messages(self):
    
        # this router does nothing except record incoming messages, to
        # ensure that .incoming_message is called during this test.
        class MockRouter(object):
            def __init__(self):
                self.msgs = []
    
            def incoming_message(self, msg):
                self.msgs.append(msg)
    
        msg = object()
        router = MockRouter()
        backend = BackendStub(router, "mock")
    
        backend.route(msg)
        self.assertEqual(router.msgs, [msg])

    def test_backend_finds_valid_backend_classes(self):
        backend = BackendBase.find('rapidsms.backends.bucket')
        from rapidsms.backends.bucket import BucketBackend
        self.assertEqual(backend, BucketBackend)
    
    def test_backend_can_be_started_and_stopped(self):
        backend = BackendStub(None, "mock")
        self.assertEqual(backend.running, False)
    
        start_delay = 0
        stop_delay = 0
        die_delay = 0
    
        # start the backend in a temporary thread, and check that it sets
        # the 'running' flag within a second. this is arbitrary, but so is
        # pretty much everything else about the multi-threaded router.
    
        worker = threading.Thread(target=backend.start)
        worker.daemon = True
        worker.start()
    
        while (backend.running is not True) and (start_delay < 1):
            start_delay += 0.1
            time.sleep(0.1)
    
        assert (start_delay < 1), "backend didn't start"
        self.assertEqual(backend.running, True)
    
        # now tell the backend to stop, and check that it did.
    
        backend.stop()
    
        while (backend.running is True) and (stop_delay < 1):
            stop_delay += 0.1
            time.sleep(0.1)
    
        assert (stop_delay < 1), "backend didn't stop"
        self.assertEqual(backend.running, False)
    
        # wait for the thread to die, to ensure that backend isn't blocking.
    
        while worker.is_alive() and (die_delay < 1):
            die_delay += 0.1
            time.sleep(0.1)
    
        assert die_delay < 1, "worker thread didn't die"
