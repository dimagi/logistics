from django.test import TestCase
import time
import threading
from ..backends.base import BackendBase
from ..apps.base import AppBase
from ..router import Router


class RouterTest(TestCase):
    def test_router_finds_apps(self):
        router = Router()
        router.add_app("rapidsms.contrib.default")
        from rapidsms.contrib.default.app import App

        self.assertEqual(len(router.apps), 1)
        app = router.get_app("rapidsms.contrib.default")

        self.assertEqual(type(app), App)


    def test_router_returns_none_on_invalid_apps(self):
        self.assertEqual(Router().get_app("not.a.valid.app"), None)


    def test_router_raises_on_uninstalled_apps(self):
        with self.assertRaises(KeyError):
            Router().get_app("rapidsms.contrib.default")

    def test_router_starts_and_stops_apps_and_backends(self):
        class MockApp(AppBase):
            def start(self):
                self.started = True

            def stop(self):
                self.stopped = True

        class MockBackend(BackendBase):
            def start(self):
                self.started = True
                BackendBase.start(self)

            def stop(self):
                self.stopped = True
                BackendBase.stop(self)

        router = Router()
        app = MockApp(router)
        router.apps.append(app)
        backend = MockBackend(router, "mock")
        router.backends["mock"] = backend

        assert hasattr(app, 'started') == False
        assert hasattr(app, 'stopped') == False
        assert hasattr(backend, 'started') == False
        assert hasattr(backend, 'stopped') == False

        # start in a separate thread, so we can test it asynchronously.
        worker = threading.Thread(target=router.start)
        worker.daemon = True
        worker.start()

        # wait until the router has started.
        while not router.running:
            time.sleep(0.1)

        self.assertEqual(app.started, True)
        self.assertEqual(backend.started, True)
        assert hasattr(app, 'stopped') == False
        assert hasattr(backend, 'stopped') == False

        # wait until the router has stopped.
        router.stop()
        worker.join()

        self.assertEqual(app.started, True)
        self.assertEqual(app.stopped, True)
        self.assertEqual(backend.started, True)
        self.assertEqual(backend.stopped, True)


    def test_router_finds_backends(self):
        router = Router()
        test_backend = "rapidsms.backends.base"
        backend = router.add_backend("mock", test_backend)

        self.assertEqual(router.backends["mock"], backend)
        self.assertEqual(len(router.backends), 1)


    def test_router_downcases_backend_configs(self):
        router = Router()
        test_backend = "rapidsms.backends.base"
        test_conf = { "a": 1, "B": 2, "Cc": 3 }

        backend = router.add_backend("mock", test_backend, test_conf)

        self.assertEqual(len(backend._config), 3)
        self.assertEqual("a"  in backend._config, True)
        self.assertEqual("b"  in backend._config, True)
        self.assertEqual("cc" in backend._config, True)
        self.assertEqual("B"  in backend._config, False)
        self.assertEqual("Cc" in backend._config, False)
