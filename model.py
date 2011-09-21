import time

from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, \
        Column, Integer, Text, ForeignKey, \
        DateTime
from sqlalchemy.sql.expression import *
from sqlalchemy.interfaces import PoolListener

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
    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')

def init(dburi):
    global Engine
    global Session

    Engine = create_engine(dburi, listeners=[ForeignKeysListener()])
    Base.metadata.bind = Engine
    Base.metadata.create_all()
    Session = sessionmaker(bind=Engine)

