# vim: set fileencoding=utf-8
import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import get_appsettings, setup_logging

from ..models import DBSession, Message, Vote, Base

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        message_a = Message(u'test meddelande', 59.375868, 17.939816)
        message_b = Message(u'ett lite längre meddelande som jag skrev precis nu, varför gjorde jag det?', 59.374973, 17.942905)
        answer_a = Message(u'det här är ett svar', 59.379323, 17.73452, parent=message_a)

        vote_1 = Vote(message_a, vote_type=True)
        vote_2 = Vote(message_a, vote_type=True)
        vote_3 = Vote(message_a, vote_type=False)

        DBSession.add_all([message_a, message_b, answer_a, vote_1, vote_2, vote_3])
