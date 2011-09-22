import time

from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, \
        Column, Integer, Text, ForeignKey, \
        DateTime
from sqlalchemy.sql.expression import *
from sqlalchemy.interfaces import PoolListener

# sqlalchemy 0.7.x throws deprecation errors if use the
# listeners= keyword on create_engine.  The ``listen`` function
# is the preferred replacement.
try:
    from sqlalchemy.event import listen
except ImportError:
    listen = None

Base = declarative_base()
Session = None
Engine = None

class Project (Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Text(), unique=True)
    work = relationship('Work', backref='project', 
            cascade='all,delete-orphan')

class Work (Base):
    __tablename__ = 'worklog'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id',
        ondelete='CASCADE'), nullable=False)
    comment = Column(Text())
    time_start = Column(DateTime(), server_default=text('current_timestamp'))
    time_stop = Column(DateTime())

# From http://stackoverflow.com/questions/2614984/sqlite-sqlalchemy-how-to-enforce-foreign-keys
# XXX: This may break with non-SQLite data sources.
class ForeignKeysListener(PoolListener):
    def __call__(self, *args):
        '''The listen() function in SQLAlchemy 0.7.x wants a callable,
        while the listeners= keywrod in 0.6.x appears to want a
        class instance.  We can give them both.'''

        return self.connect(*args)

    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')

def init(dburi):
    global Engine
    global Session

    if listen is None:
        Engine = create_engine(dburi, listeners=[ForeignKeysListener()])
    else:
        Engine = create_engine(dburi)
        listen(Engine, 'connect', ForeignKeysListener())

    Base.metadata.bind = Engine
    Base.metadata.create_all()
    Session = sessionmaker(bind=Engine)

