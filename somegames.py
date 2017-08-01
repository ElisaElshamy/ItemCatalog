from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Genre, Base, Games
 
engine = create_engine('sqlite:///videogames.db')
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



genre1 = Genre(name = "Crossover")

session.add(genre1)
session.commit()

game1 = Games(title = "Super Smash Brothers Wii U", description = "Fighting video games developed by Sora Ltd. and Bandai Namco Games, with assistance from tri-Crescendo,[6] and published by Nintendo for the Nintendo 3DS and Wii U video game consoles.", boxart="somefile/sommewhere", genre = genre1)

session.add(game1)
session.commit()


genre2 = Genre(name = "Adventure")

session.add(genre2)
session.commit()

game2 = Games(title = "The Legend of Zelda Twilight Princess HD", description = "The Legend of Zelda: Twilight Princess HD is an action-adventure game in Nintendo's The Legend of Zelda series for the Wii U home video game console.", boxart="somefile/sommewhere", genre = genre2)

session.add(game2)
session.commit()


genre3 = Genre(name = "First-Person Shooter")

session.add(genre3)
session.commit()

game3 = Games(title = "Borderlands 2", description = "Borderlands 2 is an open world, action role-playing first-person shooter video game developed by Gearbox Software and published by 2K Games.", boxart="somefile/sommewhere", genre = genre3)

session.add(game3)
session.commit()



