#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json, sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime
from model import db, Artist, Show, Venue
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# TODO: connect to a local postgresql database
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
  return babel.dates.format_datetime(date, format)

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
  """Lists all Venues which are existant (GET)
  Args:
    NONE
  Returns:
    result_list: List of venues by city and state (groupped by city and state) in a html page
  """
  result_list = []
  city_state = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
  #print(city_state)
  for i in city_state:
    d = {}
    venues = Venue.query.filter_by(city=i.city, state=i.state).all()
    d['city'] = i.city
    d['state'] = i.state
    d['venues'] = venues
    result_list.append(d)
  return render_template('pages/venues.html', areas=result_list);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  """Receives the search_term of the form and searches all venues (POST) by name (case-insensitive)
  Args:
    search_term: field from the HTML Form
  Returns:
    response: On a POST request, lists out the search results of the specifiy query. Renders it as HTML page.
  """
  search_term = request.form['search_term']
  answer_list = []
  cnt = 0
  q_string = f'%{search_term}%'
  answer = Venue.query.filter(Venue.name.ilike(q_string)).all()
  cnt = len(answer)
  for a in answer:
    e = {}
    e['id'] = a.id
    e['name'] = a.name
    answer_list.append(e)
  response={
    "count": cnt,
    "data": answer_list
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  """Shows details of a venue
  ARGS:
    venue_id int - The venue-id of choice
  RETURNS:
    d dict - a dictionary of a venue with details about it and its past and upcoming shows rendered in a HTML page.
  """
  current_time = datetime.datetime.now()
  this_venue = Venue.query.filter_by(id=venue_id).first()
  
  this_venues_shows = Show.query.filter_by(venue_id=venue_id).all()
  past_shows = []
  upcoming_shows = []
  for s in this_venues_shows:
    this_artist = Artist.query.filter_by(id=s.artist_id).first()
    s_dict = {}
    s_dict['artist_id'] = s.artist_id
    s_dict['artist_name'] = this_artist.name
    s_dict['artist_image_link'] = this_artist.image_link
    s_dict['start_time'] = s.start_time.strftime("%Y-%m-%d %H:%M:%S")
    if s.start_time < current_time:
      # Past
      past_shows.append(s_dict)
    else:
      # Future
      upcoming_shows.append(s_dict)
  
  past_shows_count = len(past_shows)
  upcoming_shows_count = len(upcoming_shows)
  d = {}
  d['id'] = this_venue.id
  d['name'] = this_venue.name
  d['genres'] = this_venue.genres
  d['address'] = this_venue.address
  d['city'] = this_venue.city
  d['state'] = this_venue.state
  d['phone'] = this_venue.phone
  d['website'] = this_venue.website
  d['facebook_link'] = this_venue.facebook_link
  d['seeking_talent'] = this_venue.seeking_talent
  d['seeking_description'] = this_venue.seeking_description
  d['image_link'] = this_venue.image_link
  d['past_shows'] = past_shows
  d['upcoming_shows'] = upcoming_shows
  d['past_shows_count'] = past_shows_count
  d['upcoming_shows_count'] = upcoming_shows_count
  
  return render_template('pages/show_venue.html', venue=d)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  """create a new venue in the database (POST) 
  ARGS:
    all form based:
      name
      city
      state
      address
      phone
      genres
      facebook_link
  RETURNS:
    Error 505 if the db insert did not succeed
    rendered home page if everything went well with a success message
  """
  error = False
  body = {}
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    
    venue = Venue(name=name,city=city,state=state,address=address,phone=phone,facebook_link=facebook_link, genres=genres)
    db.session.add(venue)
    db.session.commit()
    body['id'] = venue.id
    body['name'] = venue.name
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
    flash('Error: Venue ' + request.form['name'] + ' was not successfully listed!')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  """deletes the venue of choice (DELETE)
  ARGS:
    venue_id int - the venue id which should be deleted
  RETURNS:
    Success-Message if deletion went well
    Error 505 if the venue could not be deleted
  """
  error = False
  try:
    venue_delete = Venue.query.filter_by(id=venue_id).first()
    print(venue_delete)
    db.session.delete(venue_delete)
    db.session.commit()
    flash('Venue ' + venue_delete.name + ' was successfully deleted!')

  except:
    error = True
    print('ran into some error')
    print(sys.exc_info())
    db.session.rollback()
    flash('Venue ' + venue_delete.name + ' was NOT successfully deleted!')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  """Lists all the artists which there are
  ARGS:
    NONE
  RETURNS:
    list_of_artists rendered HTML page of all artists.
  """
  list_of_artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=list_of_artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  """searches by name via the search_term (POST) and lists the results found. 
  The search is made case insensitive
  ARGS:
    search_term (by form)
  RETURNS:
    a rendered html page of the search result.
  """
  search_term = request.form['search_term']
  answer_list = []
  cnt = 0
  q_string = f'%{search_term}%'
  answer = Artist.query.filter(Artist.name.ilike(q_string)).all()
  cnt = len(answer)
  for a in answer:
    e = {}
    e['id'] = a.id
    e['name'] = a.name
    answer_list.append(e)
  response={
    "count": cnt,
    "data": answer_list
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  """Shows details of an artist (POST)
  ARGS:
    artist_id int - The artist_id of choice
  RETURNS:
    d dict - a dictionary of an artist with details about it and its past and upcoming shows rendered in a HTML page.
  """
  current_time = datetime.datetime.now()
  this_artist = Artist.query.filter_by(id=artist_id).first()
  all_shows = Show.query.filter_by(artist_id=artist_id).all()
  past_shows = []
  upcoming_shows = []
  for s in all_shows:
    this_venue = Venue.query.filter_by(id=s.venue_id).first()
    v_dict = {}
    v_dict['venue_id'] = s.venue_id
    v_dict['venue_name'] = this_venue.name
    v_dict['venue_image_link'] = this_venue.image_link
    v_dict['start_time'] = s.start_time.strftime("%Y-%m-%d %H:%M:%S")
  
    if s.start_time < current_time:
      # Past
      past_shows.append(v_dict)
    else:
      # Future
      upcoming_shows.append(v_dict)
  
  past_shows_count = len(past_shows)
  upcoming_shows_count = len(upcoming_shows)
  d = {}
  d['id'] = this_artist.id
  d['name'] = this_artist.name
  d['genres'] = this_artist.genres
  d['city'] = this_artist.city
  d['state'] = this_artist.state
  d['phone'] = this_artist.phone
  d['website'] = this_artist.website
  d['facebook_link'] = this_artist.facebook_link
  d['seeking_venue'] = this_artist.seeking_venue
  d['seeking_description'] = this_artist.seeking_description
  d['image_link'] = this_artist.image_link
  d['past_shows'] = past_shows
  d['upcoming_shows'] = upcoming_shows
  d['past_shows_count'] = past_shows_count
  d['upcoming_shows_count'] = upcoming_shows_count

  return render_template('pages/show_artist.html', artist=d)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  this_artist = Artist.query.filter_by(id=artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=this_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  """Edits an artist by a specified artist_id.
  ARGS:
    artist_id int - The artist_id which should be updated (POST)
    via form:
      name
      city
      state
      phone
      genres
      facebook_link
  RETURNS:
    The updated Artist information in a HTML page.
  """
  try:
    this_artist = Artist.query.filter_by(id=artist_id).first()
    this_artist.name = request.form['name']
    this_artist.city = request.form['city']
    this_artist.state = request.form['state']
    this_artist.phone = request.form['phone']
    this_artist.genres = request.form.getlist('genres')
    this_artist.facebook_link = request.form['facebook_link']
    db.session.add(this_artist)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  this_venue = Venue.query.filter_by(id=venue_id).first()
  return render_template('forms/edit_venue.html', form=form, venue=this_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  """Edits a venue by a specified venue_id.
  ARGS:
    venue_id int - The venue_id which should be updated (POST)
    via form:
      name
      city
      state
      address
      phone
      genres
      facebook_link
  RETURNS:
    The updated Venue information in a HTML page.
  """
  try:
    this_venue = Venue.query.filter_by(id=venue_id).first()
    this_venue.name = request.form['name']
    this_venue.city = request.form['city']
    this_venue.state = request.form['state']
    this_venue.address = request.form['address']
    this_venue.phone = request.form['phone']
    this_venue.genres = request.form.getlist('genres')
    this_venue.facebook_link = request.form['facebook_link']
    db.session.add(this_venue)
    db.session.commit()
  except:
    db.session.rollback()
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
  """Creates a new artist (POST) with the supplied fields
  ARGS:
    via form:
      name
      city
      state
      phone
      genres
      facebook_link
  RETURNS:
    ON SUCCESS - The created Artist information in a HTML page - with a successful message
    ON Error - An error 500 message
  """
  error = False
  body = {}
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    artist = Artist(name=name,city=city,state=state,phone=phone,facebook_link=facebook_link, genres=genres)
    db.session.add(artist)
    db.session.commit()
    body['id'] = artist.id
    body['name'] = artist.name
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
    flash('Error: Artist ' + request.form['name'] + ' was not successfully listed!')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  """Return all shows that there are in the database
  ARGS:
    NONE
  RETURNS:
    result_set dict  - A rendered html page with the result_set of all shows
  """  
  all_shows = db.session.query(Show, Venue, Artist).join(Venue, Artist).all()
  result_set = []
  for s in all_shows:
    d= {}
    d['venue_id'] = s.Venue.id
    d['venue_name'] = s.Venue.name
    d['artist_id'] = s.Artist.id
    d['artist_name'] = s.Artist.name
    d['artist_image_link'] = s.Artist.image_link
    d['start_time'] = str(s.Show.start_time)
    result_set.append(d)
  
  return render_template('pages/shows.html', shows=result_set)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  """Creates a new show (POST)
  ARGS:
    all from form:
      artist_id int
      venue_id int
      start_time datetime
  RETURNS:
    ON SUCCESS - A success-message and get returned on the home page
    ON ERROR - An error-message (500)
  """
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
    flash('Error: Show was NOT successfully listed!')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
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
