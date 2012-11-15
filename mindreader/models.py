import datetime
import uuid

from sqlalchemy import Column, Integer, Numeric, Unicode, ForeignKey, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref, synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.types import TypeDecorator, CHAR

from zope.sqlalchemy import ZopeTransactionExtension

from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement

from passlib.context import CryptContext


password_context = CryptContext(
    schemes=['bcrypt'],
    all__vary_rounds = 0.1,
)


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(64))
    _password = Column('password', Unicode(128))
    email = Column(Unicode(), unique=True)
    active = Column(Boolean, default=False)
    created = Column(DateTime, default=datetime.datetime.now)

    def _set_password(self, password):
        self._password = password_context.encrypt(password)

    def _get_password(self):
        return self._password

    password = synonym('_password', descriptor=property(_get_password, _set_password))

    def __init__(self, email):
        self.email = email

    @classmethod
    def verify_by(cls, **kwargs):
        if kwargs.has_key('id'):
            user = cls.get_by_id(kwargs['id'])
        if kwargs.has_key('email'):
            user = cls.get_by_email(kwargs['email'])

        if not user:
            return False

        return password_context.verify(kwargs['password'], user.password)

    @classmethod
    def get_by_id(cls, id):
        """
        Returns User object or None by id.
        """
        return DBSession.query(cls).filter(cls.id==id).first()

    @classmethod
    def get_by_username(cls, username):
        """
        Returns User object or None by username.
        """
        return DBSession.query(cls).filter(cls.username==username).first()

    @classmethod
    def get_by_email(cls, email):
        """
        Returns User object or None by email.
        """
        return DBSession.query(cls).filter(cls.email==email).first()

    def __unicode__(self):
        return '<%s, %s>' % (self.username, self.email)


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value)
            else:
                # hexstring
                return "%.32x" % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class Vote(Base):
    """
    Votes
    """
    __tablename__ = 'votes'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    vote_type = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.datetime.now)

    message = relationship('Message', backref=backref('votes', order_by=id))
    user = relationship('User', backref=backref('votes', order_by=id))

    def __init__(self, message, user_id=None, vote_type=True):
        self.message = message
        self.user_id = user_id
        self.vote_type = vote_type

        if self.vote_type:
            self.message.positive_votes += 1
            self.message.total_votes += 1
        else:
            self.message.negative_votes += 1
            self.message.total_votes -= 1

    def __repr__(self):
        return 'Vote(message_id=%s, user_id=%s)' % (self.message_id, self.user_id)


class Message(Base):
    """
    Messages
    """
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey(id))
    user_id = Column(Integer, ForeignKey('users.id'))
    identifier = Column(GUID, default=uuid.uuid4)
    message = Column(Unicode, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    geom = Column(Geography('POINT', srid=4326))
    positive_votes = Column(Integer, nullable=False, default=0)
    negative_votes = Column(Integer, nullable=False, default=0)
    total_votes = Column(Integer, nullable=False, default=0)

    children = relationship('Message',
                            cascade='all',
                            backref=backref('parent', remote_side=id),
                            collection_class=attribute_mapped_collection('identifier'))
    user = relationship('User', backref=backref('messages', order_by=id))

    def __init__(self, message, latitude, longitude, user=None, parent=None):
        self.message = message
        self.latitude = latitude
        self.longitude = longitude
        self.geom = WKTElement('POINT(%s %s)' % (latitude, longitude))
        self.user = user
        self.parent = parent

        self.positive_votes = 0
        self.negative_votes = 0
        self.total_votes = 0

    @classmethod
    def get_by_id(cls, message_id):
        return DBSession.query(cls).filter(cls.id==message_id).first()

    @classmethod
    def get_by_identifier(cls, identifier):
        return DBSession.query(cls).filter(cls.identifier==identifier).first()

    @classmethod
    def get_for_coordinates(cls, latitude, longitude, distance=2000):
        point = WKTElement('POINT(%s %s)' % (latitude, longitude))
        query = DBSession.query(cls.identifier,
                                cls.message,
                                cls.created,
                                func.ST_Distance(point, cls.geom).label('distance'),
                                cls.total_votes,
                                cls.positive_votes,
                                cls.negative_votes) \
                         .filter(cls.geom.ST_DWithin(point, distance)) \
                         .order_by(cls.created.desc())

        return query

    @classmethod
    def get_for_parent(cls, latitude, longitude, parent):
        message = DBSession.query(cls).filter(cls.identifier==parent).subquery('message')
        query = DBSession.query(cls.identifier,
                                cls.message,
                                cls.created,
                                cls.total_votes,
                                cls.positive_votes,
                                cls.negative_votes) \
                         .filter(cls.parent_id==message.c.id) \
                         .order_by(cls.created.asc())

        return query

    def __json__(self, request):
        return {'message': self.message,
                'created': str(self.created),
                'latitude': str(self.latitude),
                'longitude': str(self.longitude),
                'parent': self.parent}

    def __repr__(self):
        return 'Message(id=%s, parent=%s)' % (self.id, self.parent_id)

    def dump(self, indent=0):
        return '  ' * indent + repr(self) + '\n' + ''.join([c.dump(indent + 1) for c in self.children.values()])
