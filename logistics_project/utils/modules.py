from __future__ import unicode_literals


def to_function(function_path, failhard=False):
    """
    Convert a string like foo.bar.baz into a function (assumes that
    baz is a function defined in foo/bar.py).
    """
    try:
        # TODO: make this less brittle if imports or args don't line up
        module, func = function_path.rsplit(".", 1)
        module = __import__(module, globals(), locals(), [func])
        actual_func = getattr(module, func)
        return actual_func
    except ImportError:
        if failhard:
            raise
