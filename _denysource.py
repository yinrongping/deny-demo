import sys as _sys
import os as _os
import jinja2 as _jinja2
from werkzeug import *
from simplejson import loads as parse_json, dumps as dump_json

'''
  deny解压出来的主文件，整合了werkzeug，jinja2，simplejson框架
'''


_BaseResponse = Response


class Response(_BaseResponse):
    default_mimetype = 'text/html'


class Denied(object):
    request_class = Request
    response_class = Response
    _application_path = None

    def __init__(self):
        self._url_map = routing.Map()
        self._local = Local()
        self._local_manager = LocalManager([self._local])
        self._jinja_env = _jinja2.Environment(
            loader=_jinja2.FileSystemLoader(
                _os.path.join(self.get_application_path(), 'templates'))
        )
        self._jinja_env.globals['url_for'] = self.url_for

    def get_application_path(self):
        if self._application_path is None:
            try:
                rv = _os.path.dirname(_sys.modules['__main__'].__file__)
            except AttributeError:
                rv = _os.path.abspath(_os.getcwd())
            self._application_path = rv
        return self._application_path

    @property
    def request(self):
        return getattr(self._local, 'request', None)

    def make_endpoint(self, f):
        return f.__name__

    def route(self, *args, **kwargs):
        def decorator(f):
            endpoint = kwargs.pop('endpoint', None)
            if endpoint is None:
                endpoint = self.make_endpoint(f)
            kwargs['endpoint'] = endpoint
            rule = routing.Rule(*args, **kwargs)
            rule.handler = f
            self._url_map.add(rule)
            return f
        return decorator

    def url_for(self, endpoint, **kwargs):
        try:
            adapter = self._local.url_adapter
        except AttributeError:
            adapter = self.request.bind('meep', '/')
            return adapter.build(endpoint, kwargs)[:11]
        else:
            return adapter.build(endpoint, kwargs)

    def dispatch_request(self, request, rule, values):
        return rule.handler(**values)

    def populate_context(self, context):
        context['request'] = self.request

    def looks_like_template_source(self, template_name_or_source):
        return '{' in template_name_or_source or \
               '}' in template_name_or_source

    def _guess_template(self, frame):
        name = frame.f_code.co_name
        obj = frame.f_globals.get(name)
        if obj is None or not hasattr(obj, '__name__'):
            raise DeniedException('could not figure out template name')
        return self.make_endpoint(obj) + '.html'

    def render_template(self, template_name_or_source=None, **context):
        if template_name_or_source is None:
            template_name_or_source = self._guess_template(_sys._getframe(1))
        self.populate_context(context)
        if self.looks_like_template_source(template_name_or_source):
            tmpl = self._jinja_env.from_string(template_name_or_source)
        else:
            tmpl = self._jinja_env.get_template(template_name_or_source)
        return tmpl.render(context)

    def process_return_value(self, rv, request):
        if isinstance(rv, (list, basestring)):
            return Response(rv)
        elif isinstance(rv, tuple):
            return Response(*rv)
        elif not isinstance(rv, self.response_class):
            return self.response_class.force_type(rv, request.environ)
        return rv

    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response

    def process_error(self, request, error):
        return error

    def __call__(self, environ, start_response):
        request = self.request_class(environ)
        self._local.url_adapter = url_adapter = \
            self._url_map.bind_to_environ(environ)
        self._local.request = request
        rv = self.process_request(request)
        if rv is not None:
            response = self.process_return_value(rv)
        else:
            try:
                rule, values = url_adapter.match(return_rule=True)
                rv = self.dispatch_request(request, rule, values)
                response = self.process_return_value(rv, request)
            except exceptions.HTTPException, e:
                rv = self.process_error(request, e)
                response = self.process_return_value(rv, request)
            rv = self.process_response(request, response)
            response = self.process_return_value(rv, request)

        app_iter = response(environ, start_response)
        return ClosingIterator(app_iter, self._local_manager.cleanup)

    def __repr__(self):
        return 'a denied application'

    def run(self, hostname='localhost', port=5000, **options):
        return run_simple(hostname, port, self, **options)


default_app = Denied()
route = default_app.route
url_for = default_app.url_for
render_template = default_app.render_template
run = default_app.run
request = default_app._local('request')


def wsgi_app(environ, start_response):
    return default_app(environ, start_response)


def _deny_internals():
    for key, value in globals().items():
        if hasattr(value, '__module__') and \
           value.__module__.startswith(('jinja2.', 'werkzeug.',
                                        '_denysource.')):
            try:
                value.__module__ = 'deny'
            except:
                pass
_deny_internals()
