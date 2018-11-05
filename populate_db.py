from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from database_setup import Base, Category, User, Item

engine = create_engine('postgresql://tom:football8@localhost/catalog')
#engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# add categories
myFirstCategory = Category(name = 'New York')
session.add(myFirstCategory)
session.commit()

mySecondCategory = Category(name = 'Chicago')
session.add(mySecondCategory)
session.commit()

myThirdCategory = Category(name = 'Los Angeles')
session.add(myThirdCategory)
session.commit()

myFourthCategory = Category(name = 'Dallas')
session.add(myFourthCategory)
session.commit()

myFifthCategory = Category(name = 'Washington DC')
session.add(myFifthCategory)
session.commit()



# add user
myFirstUser = User(name = 'ryan', email="ryan.w.boehm@gmail.com", picture = 'https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(myFirstUser)
session.commit()



# add items
myFirstItem = Item(name = 'Pizza', description = 'classic italian pizza', author_id = 1,
    category = myFirstCategory, created = datetime.now(), updated = datetime.now())
session.add(myFirstItem)
session.commit()

mySecondItem = Item(name = 'Ramen', description = 'excellent noodle dish', author_id = 1,
    category = myFirstCategory, created = datetime.now(), updated = datetime.now())
session.add(mySecondItem)
session.commit()

myThirdItem = Item(name = 'Pasta', description = 'excellent italian pasta dish', author_id = 1,
    category = mySecondCategory, created = datetime.now(), updated = datetime.now())
session.add(myThirdItem)
session.commit()

myFourthItem = Item(name = 'Hamburgers', description = 'classic american food', author_id = 1,
    category = mySecondCategory, created = datetime.now(), updated = datetime.now())
session.add(myFourthItem)
session.commit()

myFifthItem = Item(name = 'Seafood', description = 'clam chowder and other specialties', author_id = 1,
    category = myThirdCategory, created = datetime.now(), updated = datetime.now())
session.add(myFifthItem)
session.commit()

mySixthItem = Item(name = 'Sandwiches', description = 'bare bones lunch specials', author_id = 1,
    category = myThirdCategory, created = datetime.now(), updated = datetime.now())
session.add(mySixthItem)
session.commit()

mySeventhItem = Item(name = 'Chinese food', description = 'hunan beef and lomein dishes', author_id = 1,
    category = myFourthCategory, created = datetime.now(), updated = datetime.now())
session.add(mySeventhItem)
session.commit()

myEigthItem = Item(name = 'Sushi', description = 'raw seafood', author_id = 1,
    category = myFourthCategory, created = datetime.now(), updated = datetime.now())
session.add(myEigthItem)
session.commit()
