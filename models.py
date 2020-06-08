from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


from flask_sqlalchemy import SQLAlchemy

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer(), primary_key = True, nullable = False)
    username = Column(String(), nullable = False, unique = True)
    password = Column(String(), nullable = False)

    def __repr__(self):
        return '<User(id = '%i', username = '%s', password = '%s')>' % (
                                self.id, self.username, self.password)

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer(), primary_key = True, nullable = False)
    channel = Column(String(), nullable = False, unique = True)
    created_by = Column(Integer(), ForeignKey('user.id'))

    user = relationship(User, backref = 'channel', lazy = True)


    def __repr__(self):
        return '<Channel(channel = '%s')>' % (self.channel)

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer(), primary_key = True, nullable = False)
    user_id = Column(Integer(), ForeignKey('user.id'), index = True, nullable = False)
    channel = Column(String(), ForeignKey('channel.channel'), nullable = False)
    message = Column(String(), nullable = False)
    timestamp = Column(DateTime, default = datetime.utcnow)

    user = relationship(User, backref='Message', lazy = True)

    def __repr__(self):
        return '<Message(id = '%i', user_id = '%i', channel = '%s', message = '%s')>' % (
                         self.id, self.user_id, self.channel, self.message)