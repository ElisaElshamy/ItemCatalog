import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
 
class Genre(Base):
    __tablename__ = 'genre'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    creator_id = Column(Integer, ForeignKey('user.id'))
    creator = relationship(User)
 
class Games(Base):
    __tablename__ = 'games'

    title =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    boxart = Column(String(256))
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre)
    creator_id = Column(Integer, ForeignKey('user.id'))
    creator = relationship(User)
 
    # We added this serialize function to be able to send JSON objects in a
    # serializable format
    @property
    def serialize(self):

        return {
            'title': self.title,
            'description': self.description,
            'id': self.id,
            'boxart': self.boxart,
            'genre': self.genre.name,
        }

engine = create_engine('sqlite:///videogames.db')
Base.metadata.create_all(engine)