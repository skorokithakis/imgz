from django.core.handlers.wsgi import WSGIHandler

from imgz import wsgi


def test_wsgi_sorta_works():
    """
    Slightly stupid test to ensure that imgz/wsgi.py is not completely broken
    and somewhat resembles what a WSGI application is.
    """
    assert isinstance(wsgi.application, WSGIHandler)
