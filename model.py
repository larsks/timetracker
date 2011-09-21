import time

from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, \
        Column, Integer, Text, ForeignKey, \
        DateTime
from sqlalchemy.sql.expression import *

Base = declarative_base()
Session = None
Engine = None

class Project (Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(Text(), unique=True)
    work = relationship('Work', backref='project')

class Work (Base):
    __tablename__ = 'worklog'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    comment = Column(Text())
    time_start = Column(DateTime(), server_default=text('current_timestamp'))
    time_stop = Column(DateTime())

def init(dburi):
    global Engine
    global Session

    Engine = create_engine(dburi)
    Base.metadata.bind = Engine
    Base.metadata.create_all()
    Session = sessionmaker(bind=Engine)

