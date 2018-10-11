# Udacity Project 4: Item Catalog Application
This project displays items by category.  The home page displays all of the categories in the left column,
and all of the items in the right column.  The user has the option to add a new item by clicking the "Add Item"
link near the top of the right column.  When the user clicks on a category, the center column only shows
the items associated with the chosen category.  Alternatively, when the user clicks on an item, the page only shows
the content associated with the chosen item.  If the user authored the item in question, then edit and delete links
will appear below the item's content.  The application uses google plus and facebook for oauth2 authentication.

## Usage
Install VirtualBox - https://www.virtualbox.org/wiki/Downloads
Install Vagrant - https://www.vagrantup.com/downloads.html
Run `vagrant up` from inside the vagrant subdirectory to build the environment
Run  `python database_setup.py` to set-up the structure of the database
Run `python populate_db.py` to populate the database initially
Run `python application.py` to run the application
Visit http://localhost:5000 to interact with and use the application

## Dependencies
* VirtualBox
* vagrant
* sqlite
* psycopg2
* sqlalchemy
* werkzeug==0.8.3
* flask==0.9
* Flask-Login==0.1.3
* oauth2client
* requests
* httplib2
* json
* date_time
