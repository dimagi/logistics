from django.test import TestCase
import time
import threading
from ...router import Router

class BucketTest(TestCase):
    
    def test_bucket_swallows_messages(self):

        router = Router()
        router.add_backend("mock", "rapidsms.backends.bucket")
        worker = threading.Thread(target=router.start)
        worker.daemon = True
        worker.start()

        # wait until the router has started.
        while not router.running:
            time.sleep(0.1)

        backend = router.backends["mock"]
        backend.receive("1234", "Mock Incoming Message")

        msg = object()
        backend.send(msg)

        self.assertEqual(backend.bucket[0].text, "Mock Incoming Message")
        self.assertEqual(backend.bucket[1], msg)
        self.assertEqual(len(backend.bucket), 2)

        # wait until the router has stopped.
        router.stop()
        worker.join()
