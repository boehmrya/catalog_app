from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, User, Item


#Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# start db session
DBSession = sessionmaker(bind=engine)
session = DBSession()


#Show home page
@app.route('/')
def showHome():
  categories = session.query(Category).order_by(asc(Category.name)).limit(10)
  items = session.query(Item).join(Item.category)
  return render_template('home.html', categories = categories, items = items)



#Show category page
@app.route('/catalog/<category_name>')
def showCategory(category_name):
  items = session.query(Item).filter_by(name = category_name).order_by(asc(created)).limit(10)
  return render_template('category.html', categories = categories, items = items)



#Show item page
@app.route('/item/<item_name>')
def showItem(item_name):
  items = session.query(Item).filter_by(name = item_name).one()
  return render_template('item.html', item)



#Create a new item
@app.route('/item/new/', methods=['GET','POST'])
def newItem():
  if request.method == 'POST':
      newItem = Item(name = request.form['name'])
      session.add(newItem)
      flash('New Item %s Successfully Created' % newItem.name)
      session.commit()
      return redirect(url_for('home'))
  else:
      return render_template('newItem.html')



#Edit an item
@app.route('/catalog/<item_name>/edit/', methods = ['GET', 'POST'])
def editItem(item_name):
  editedItem = session.query(Item).filter_by(name = item_name).one()
  if request.method == 'POST':
      if request.form['name']:
        editedItem.name = request.form['name']
        flash('Item Successfully Edited %s' % editedItem.name)
        return redirect(url_for('item'))
  else:
    return render_template('editItem.html', item = editedItem)



#Delete an item
@app.route('/catalog/<item_name>/delete/', methods = ['GET','POST'])
def deleteRestaurant(item_name):
  itemToDelete = session.query(Item).filter_by(name = item_name).one()
  if request.method == 'POST':
    session.delete(itemToDelete)
    flash('%s Successfully Deleted' % itemToDelete.name)
    session.commit()
    return redirect(url_for('home'))
  else:
    return render_template('deleteItem.html', item = itemToDelete)



#JSON APIs to view Category Information
@app.route('/catalog/<category_name>/JSON')
def categoryItemsJSON(category_name):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(name = category_name).all()
    return jsonify(Items=[i.serialize for i in items])



if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
