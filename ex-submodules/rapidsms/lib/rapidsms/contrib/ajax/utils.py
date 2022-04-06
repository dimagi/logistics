from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from json import JSONDecoder

from rapidsms.conf import settings
from . import exceptions


def call_router(app, action, **kwargs):
    post = kwargs if len(kwargs) else None
    (status, content_type, body) = request("%s/%s" % (app, action), post=post)
    # if the response was encoded json, decode it before returning
    if content_type == "application/json":
        return JSONDecoder().decode(body.decode('utf-8'))

    # return plain text as-is
    elif content_type == "text/plain":
        return body

    # other content types must be dealt with by 'request'
    raise exceptions.MalformedRouterResponse(
        "The call_router helper can only return decoded JSON or plain" +\
        "text responses. The content_type was: %s" % content_type)


def request(path, get=None, post=None, encoding=None):
    """
    Send an HTTP request to the RapidSMS router, via the AJAX app (which
    must be running for this to work), and return a tuple containing the
    returned HTTP status, content-type, and body.
    """

    # build the url to the http server running in the app. encoding
    # doesn't apply here, since the query string only supports ASCII:
    # http://www.w3.org/TR/REC-html40/interact/forms.html#idx-POST-1
    query = "?%s" % urllib.parse.urlencode(get) if (get is not None) else ""
    url = "http://%s:%d/%s%s" % (
        settings.AJAX_PROXY_HOST,
        settings.AJAX_PROXY_PORT,
        path, query)

    # if *post* quacks like a QuerySet, it can urlencode itself, taking
    # its own character encoding into account. which is nice.
    if hasattr(post, "urlencode"):
        encoding = post.encoding()
        data = post.urlencode()

    # ...but if it's just a dict, we have no idea what we're encoding,
    # so let's pretend that it's the django default
    else:
        encoding = settings.DEFAULT_CHARSET
        # urlencode only takes bytes, so we need to encode
        # whatever charset we're using as bytes
        data = None
        if post is not None:
            data = urllib.parse.urlencode(post).encode(encoding)
    
    # build the content-type header, including the character set
    # that we just encoded the POST data into
    headers = {
        "content-type": "%s; charset=%s" % (
            "application/x-www-form-urlencoded",
            encoding) }

    try:

        # do the subrequest; this might raise
        req = urllib.request.Request(url, data, headers)
        res = urllib.request.urlopen(req)

        # it worked!
        content_type = res.info()["content-type"]
        return (res.code, content_type, res.read())

    # the server returned an error
    except urllib.error.HTTPError as err:
        raise exceptions.RouterError(
            err.code, err.info()["content-type"], err.read())

    # the router couldn't be reached
    except urllib.error.URLError as err:
        raise exceptions.RouterNotResponding
