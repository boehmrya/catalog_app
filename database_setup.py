from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


def _get_date():
    return datetime.now()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'           : self.id,
           'name'         : self.name,
           'email'           : self.email,
       }


class Item(Base):
    __tablename__ = 'item'


    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    author_id = Column(Integer,ForeignKey('user.id'))
    author = relationship(User)
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)
    created = Column(Date, default=_get_date)
    updated = Column(Date, onupdate=_get_date)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'description'         : self.description,
           'id'         : self.id,
       }


engine = create_engine('sqlite:///catalog.db?check_same_thread=False')

Base.metadata.create_all(engine)
