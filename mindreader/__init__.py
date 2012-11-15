import datetime

from pyramid.config import Configurator
from pyramid.renderers import JSON

from sqlalchemy import engine_from_config

from .models import DBSession, Base

json_renderer = JSON()
json_renderer.add_adapter(datetime.datetime, lambda obj, _: obj.strftime('%Y-%m-%d %H:%M:%S'))


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_renderer('json', json_renderer)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('message', '/api/message/')
    config.add_route('message_vote', '/api/message/vote/')

    config.add_route('signup', '/api/signup/')
    config.add_route('signin', '/api/signin/')
    config.add_route('signout', '/api/signout/')

    config.add_route('catch_all', '/*path')

    config.scan()
    return config.make_wsgi_app()
