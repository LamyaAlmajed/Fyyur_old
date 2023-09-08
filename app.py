#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import collections
import collections.abc
collections.Callable = collections.abc.Callable
from markupsafe import Markup
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import config
from flask_migrate import Migrate
from datetime import datetime
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)  
migrate = Migrate(app, db)


   

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')

def venues():
  data = [] # fills it with the venue data that will be shown on the page.
  places = Venue.query.all() #brings all venues from a database
  spots = set() # keeps tracking

  for place in places:
    spots.add((place.city, place.state))

  for spot in spots:
    data.append({
      "city": spot[0], "state": spot[1], "spots": []
    })

  for place in places:
    num_upcoming_shows = 0

    gigs = Show.query.filter_by(venue_id=place.id).all()
    date = datetime.now()

    for gig in gigs:
      if gig.start_time > date:
        num_upcoming_shows += 1

    for venue_place in data:
      if place.state == venue_place['state'] and place.city == venue_place['city']:
        venue_place['spots'].append({
          "id": place.id,
          "name": place.name,
          "upcoming": num_upcoming_shows
        })

  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form.get('search','') # from the submitted form data. 
  SResult = Venue.query.filter(Venue.name.like(f'%{search}%')) #searches for venues using 'like'
   
  response={
    "count": SResult.count(),
    "data": SResult}
     
  return render_template('pages/search_venues.html', results=response, search=search)

@app.route('/venues/<int:venue_id>')

def show_venue(venue_id):
    place = Venue.query.get(venue_id) # fetch venue's data from a database
    gigs = Show.query.filter_by(venue_id=venue_id).all() #show data
    oldShows = []
    newShows = []
    timeNow = datetime.now()

    for gig in gigs:
        show_data = {
            'id': gig.venue.id, # accessing the id from venue..
            'name': gig.venue.name, 
            'start': format_datetime(str(gig.start_time))
        }

        if gig.start_time > timeNow:
            newShows.append(show_data)
        else:
            oldShows.append(show_data)

    data = {
        "id": place.id,
        "name": place.name,
        "address": place.address,
        "city": place.city,
        "state": place.state,
        "phone": place.phone,
        "facebook_link": place.facebook_link,
        "image_link": place.image_link,
        "website_link": place.website_link,
        "seeking_talent": place.seeking_talent,
        "seeking_description": place.seeking_description,
        "genres": place.genres,
        "oldShows": oldShows,
        "newShows": newShows,
        "oldShows_counter": len(oldShows),
        "newShows_counter": len(newShows)
    }

    return render_template('pages/show_venue.html', place=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
     form= VenueForm()
     place = Venue(
       name=form.name.data,
       city=form.city.data, 
       state=form.state.data, 
       address= form.address.data, 
       phone=form.phone.data, 
       image_link=form.image_link.data, 
       facebook_link= form.facebook_link.data, 
       website_link=form.website_link.data, 
       seeking_talent= form.seeking_talent.data, 
       seeking_description=form.seeking_description.data, 
       genres=form.genres.data
         )
  
     db.session.add(place)
     db.session.commit()

  # on successful db insert, flash success
     flash('Venue ' + request.form['name'] + ' was successfully added!')

  except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e)) #shows what's the error exactly

  finally:
     db.session.close()

  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    place = Venue.query.get(venue_id)
    if place is None:
      flash('Error: ' + str(e))
    else:
      venue_name = place.name
      db.session.delete(place)
      db.session.commit()
      flash('The Venue ' + venue_name + ' has been removed')
    
  except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e))

  finally:
    db.session.close()

  return redirect(url_for('index'))
     

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # the singer means the artist.
  try:
    singers = Artist.query.all()
    data = []
    for singer in singers:
       data.append({
          'id': singer.id,
          'name': singer.name,
          'city': singer.city,
          'state': singer.state,
          'phone': singer.phone,
          'genres': singer.genres,
          'image_link': singer.image_link,
          'facebook_link': singer.facebook_link,
          'website_link': singer.website_link,
          'seeking_venue': singer.seeking_venue,
          'seeking_description': singer.seeking_description
       })

    return render_template('pages/artists.html', singers=data)

  except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e))

  finally:
    db.session.close()

  return redirect(url_for('home'))
  
  
@app.route('/artists/search', methods=['POST'])
def search_artists():

  search = request.form.get('search','')
  found = Artist.query.filter(Artist.name.ilike(f'%{search}%'))

  response = {
    'count': len(found),
    'data': found
  }


  return render_template('pages/search_artists.html', fount=response , search=request.form.get('search',''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  singer = Artist.query.get(artist_id)
  shows = Show.query.filter_by(artist_id=artist_id).all()
  oldShows = [] #past
  newShows = [] #upcoming
  timeNow = datetime.now()

  for show in shows:
    data = {
      'id': show.venue_id,
      'name': show.name,
      'image': show.image_link,
      'start': format_datetime(str(show.start_time))
    }

    if show.start_time > timeNow:
      newShows.append(data)
    else:
      oldShows.append(data) 

  data = {
    'id': singer.id,
    'name': singer.name,
    'city': singer.city,
    'state': singer.state,
    'phone': singer.phone,
    'genres': singer.genres,
    'image_link': singer.image_link,
    'facebook_link': singer.facebook_link,
    'website_link':singer.website_link,
    'seeking_venue': singer.seeking_venue,
    'seeking_description': singer.seeking_description,
    'oldshows': oldShows,
    'newshows': newShows,
    'timenow': timeNow
  }

  return render_template('pages/show_artist.html', singer=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  singer= Artist.query.get(artist_id)

  singer={
    "id": singer.id,
    "name": singer.name,
    "genres": singer.genres,
    "city": singer.city,
    "state": singer.state,
    "phone": singer.phone,
    #"website_link": singer.website_link,
    "facebook_link": singer.facebook_link,
    #"seeking_venue": True,
    #"seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": singer.image_link
  }
  return render_template('forms/edit_artist.html', form=form, singer=singer)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm()
    singer = Artist.query.get(artist_id)

    if singer is None:
      flash('Error: Artist not found.')
    else:
      singer.name = form.name.data
      singer.city = form.city.data
      singer.state = form.state.data
      singer.phone = form.phone.data
      singer.genres = form.genres.data
      singer.image_link = form.image_link.data
      singer.facebook_link = form.facebook_link.data
      
      db.session.commit()
      flash('Successfully updated.')

  except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e))

  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  place = Venue.query.get(venue_id)

  if place is None:
    flash('Error: Venue not found.')
    return redirect(url_for('home'))

  place = {
    "id": place.id,
    "name": place.name,
    "genres": place.genres,
    "address": place.address,
    "city": place.city,
    "state": place.state,
    "phone": place.phone,
    "website_link": place.website_link,
    "facebook_link": place.facebook_link,
    "seeking_talent": place.seeking_talent,
    "seeking_description": place.seeking_description,
    "image_link": place.image_link
  }

  return render_template('forms/edit_venue.html', form=form, place=place)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
   form = VenueForm()
   place= Venue.query.get(venue_id)
   

   place.name = form.name.data
   place.city= form.city.data
   place.state= form.state.data
   place.address= form.address.data
   place.phone= form.phone.data
   place.image_link= form.image_link.data
   place.facebook_link= form.facebook_link.data

   
   db.session.commit()
   flash("Successful.")

  except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e))

  finally:
   db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

 try:
   form= ArtistForm()
   singer= Artist(
     name=form.name.data, 
     city=form.city.data,
     state =form.state.data,
     phone= form.phone.data,
     genres= form.genres.data,
     image_link= form.image_link.data,
     facebook_link= form.facebook_link.data,
     website_link=form.website_link.data,
     seeking_venue=form.seeking_venue.data,
     seeking_description=form.seeking_description.data

  )
   
   db.session.add(singer)
   db.session.commit()

 
   flash('Artist ' + request.form['name'] + ' was successfully added!')

 except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e))
 finally: 
  db.session.close()

 return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  gigs = Show.query.order_by(db.desc(Show.start_time))
  data=[]
  for gig in gigs:
     data.append({
        'venue_id': gig.venue_id,
        'venue_name': gig.name,
        'artist_id': gig.artist.id,
        'artist_name': gig.artist.name,
        'image_link': gig.image_link,
        'start': format_datetime(str(gig.start_time))
     }) 

  return render_template('pages/shows.html', gigs=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])

def create_show_submission():
  try:
    gig = Show(
      artist_id=request.form.get('artist_id'),
      venue_id=request.form.get('venue_id'),
      start_time=request.form.get('start_time')
    )

    db.session.add(gig)
    db.session.commit()
    flash('Show was successfully added!')

  except Exception as e:
        db.session.rollback()
        flash('Error: ' + str(e))

  finally:
    db.session.close()
    return render_template('pages/home.html')
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
