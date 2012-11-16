import bisect
import json
import os.path

from pyramid.response import Response, FileResponse
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest

from .models import DBSession, Message, Vote


@view_config(route_name='catch_all')
def catch_all(request):
    """
    Catch all view that renders index.html
    """
    index = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
    return FileResponse(index, request=request)


@view_config(route_name='signup')
def signup(request):
    return ''


@view_config(route_name='signin')
def signin(request):
    return ''


@view_config(route_name='signout')
def signout(request):
    return ''


distance_map = ['0-100', '100-250', '250-500', '500-1000', '1000+']

@view_config(route_name='message', request_method='GET', renderer='json')
def message_get(request):
    latitude = request.params.get('latitude', None)
    longitude = request.params.get('longitude', None)
    parent = request.params.get('parent', None)
    if not parent:
        parent = None

    if latitude and longitude and not parent:
        messages = []
        for message in Message.get_for_coordinates(latitude, longitude).limit(20):
            messages.append({'id': message[0].hex,
                             'message': message[1],
                             'created': message[2],
                             'distance': distance_map[bisect.bisect_left([100, 250, 500, 1000], message[3])],
                             'votes': message[4]})

        return messages

    elif parent:
        messages = []
        for message in Message.get_for_parent(latitude, longitude, parent):
            messages.append({'id': message[0].hex,
                             'message': message[1],
                             'created': message[2],
                             'distance': distance_map[0],
                             'votes': message[3]})

        return messages


    raise HTTPBadRequest()


@view_config(route_name='message', request_method='POST', renderer='json')
def message_post(request):
    """
    POST handler for messages
    """
    try:
        data = json.loads(request.body)
    except ValueError, TypeError:
        raise HTTPBadRequest()

    latitude = data.get('latitude', None)
    longitude = data.get('longitude', None)
    message = data.get('message', None)
    parent = data.get('parent', None)

    if latitude and longitude and message:
        message = Message(message, latitude, longitude, parent)
        session = DBSession()
        session.add(message)
        session.flush()

        return {'id': message.identifier.hex,
                'message': message.message,
                'created': message.created,
                'distance': distance_map[0],
                'votes': 0}

    raise HTTPBadRequest()


@view_config(route_name='message_vote', request_method='POST', renderer='json')
def message_vote_post(request):
    """
    POST handler for message votes
    """
    try:
        data = json.loads(request.body)
    except ValueError, TypeError:
        raise HTTPBadRequest()

    message_id = data.get('message_id', None)
    vote_type = data.get('vote_type', None)

    if message_id and vote_type is not None:
        message = Message.get_by_identifier(message_id)

        session = DBSession()
        session.add(Vote(message, vote_type=vote_type))
        session.flush()

        return {'id': message.identifier.hex,
                'message': message.message,
                'created': message.created,
                'distance': distance_map[0],
                'total_votes': message.total_votes,
                'positive_votes': message.positive_votes,
                'negative_votes': message.negative_votes}

    raise HTTPBadRequest()
