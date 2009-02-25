#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms

if __name__ == "__main__":
    router = rapidsms.router.Router()
    conf = rapidsms.Config("config.json")

    # iterate the app names from the config,
    # and attempt to import each of them
    for app_name in conf["apps"]:
        try:
            app_module_str = "apps.%s.app" % (app_name)
            app_module = __import__(app_module_str, {}, {}, [''])
            router.add_app(app_module.App())

        # it's okay if an app couldn't be loaded
        # TODO: proper logging here (and everywhere!)
        except ImportError, err:
            print "Couldn't import app: %s" % (app_name)

    # iterate the backend names from the config,
    # and attempt to connect to each of them
    for backend_name in conf["backends"]:
        try:
            backend_module_str = "rapidsms.backends"
            backend_module = __import__(backend_module_str, {}, {}, [''])
            backend_class = backend_name.capitalize()
            # dynamically create an instance of the given
            # backend type from the corresponding backend
            # module, and pass the router to the constructor
            router.add_backend(getattr(backend_module, backend_class)(router))

        # it's okay if a backend couldn't be loaded
        # TODO: proper logging here (and everywhere!)
        except ImportError, err:
            print "Couldn't import backend: %s" % (backend_class)
        except AttributeError, err:
            print "Backend: %s does not have class: %s" % \
                (backend_name, backend_class)

    # wait for incoming sms
    router.serve_forever()
