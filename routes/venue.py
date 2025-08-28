from app import app, db
from models import Venue

from dateutil import parser
from flask import render_template, request, flash, redirect, url_for, jsonify
from forms import *
from datetime import datetime
#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  sql = """select
              v.id,
              COUNT(s.venue_id) AS num_upcoming_shows
          from
            "Venue" v
          left join "Show" s on
            v.id = s.venue_id
          GROUP BY v.id
        """

  venue_show_count = db.session.execute(sql).fetchall()
  venue_show_map = {}
  for row in venue_show_count:
    venuId = row["id"]
    num_upcoming_shows = row["num_upcoming_shows"]
    venue_show_map[venuId] = num_upcoming_shows

  sql2 = """SELECT
              city,
              state,
              json_agg(
                  json_build_object(
                      'id', id,
                      'name', name
                  )
              ) AS venues
          FROM "Venue"
          GROUP BY city, state
          ORDER BY state, city"""

  venuesByCityState = db.session.execute(sql2).fetchall()
  data = []
  for cityStateData in venuesByCityState:
    row = {}
    row["city"] = cityStateData["city"]
    row["state"] = cityStateData["state"]
    row['venues'] = []
    for venue in cityStateData["venues"]:
      venueItem = {}
      venue["new_upcoming_shows"] = venue_show_map[venue['id']] | 0
      venueItem["id"] = venue["id"]
      venueItem["name"]=  venue["name"]
      venueItem["new_upcoming_shows"] = venue["new_upcoming_shows"]
      row['venues'].append(venueItem)
    data.append(row)

    # data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')  
  sql = f"""select
          v.id,
            v.name,
          COUNT(s.venue_id) as num_upcoming_shows
        from
          "Venue" v
        left join "Show" s on
          v.id = s.venue_id
        where
          LOWER(name) like LOWER('%{search_term}%')
        GROUP BY v.id"""
  
  venuesByName = db.session.execute(sql).fetchall()
  data = []
  count = 0
  for row in venuesByName:
     count+=1
     venue = {
        "id": row["id"],
        "name": row["name"],
        "num_upcoming_shows": row["num_upcoming_shows"]
     }
     data.append(venue)

  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  response = {
     "count": count,
     "data": data 
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  # sql = f"""select v.*,
  #           json_agg(
  #                 json_build_object(
  #               'artist_id', a.id,
  #               'artist_name', a.name,
  #               'artist_image_link', a.image_link,
  #               'start_time', s.start_time
  #             )
  #             ) AS shows
  #       from "Venue" v 
  #       left join "Show" s on
  #         v.id = s.venue_id 
  #       left join "Artist" a on s.artist_id = a.id
  #       where v.id={venue_id}
  #       group by v.id"""

  sql = f"""SELECT v.*,
              COALESCE(
                json_agg(
                  json_build_object(
                    'artist_id', a.id,
                    'artist_name', a.name,
                    'artist_image_link', a.image_link,
                    'start_time', s.start_time
                  )
                ) FILTER (WHERE a.id IS NOT NULL),  -- avoid `[null]` when no artists
                '[]'::json
              ) AS shows
        FROM "Venue" v
        LEFT JOIN "Show" s ON v.id = s.venue_id
        LEFT JOIN "Artist" a ON s.artist_id = a.id
        WHERE v.id = {venue_id}
        GROUP BY v.id"""

  result = db.session.execute(sql)
  columns = result.keys()
  list = [dict(zip(columns, row)) for row in result]
  venueById = list[0]

  upcoming_shows = []
  past_shows = []
  for show in venueById["shows"]:
    start_time = parser.parse(show["start_time"])
    now = datetime.now()
    if start_time > now:
       upcoming_shows.append(show)
    else:
       past_shows.append(show)
  venueById["upcoming_shows"] = upcoming_shows
  venueById["past_shows"] = past_shows
  venueById["upcoming_shows_count"] = len(upcoming_shows)
  venueById["past_shows_count"] = len(past_shows)
  del venueById["shows"]

  data1={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    "past_shows": [{
      "artist_id": 4,
      "artist_name": "Guns N Petals",
      "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data2={
    "id": 2,
    "name": "The Dueling Pianos Bar",
    "genres": ["Classical", "R&B", "Hip-Hop"],
    "address": "335 Delancey Street",
    "city": "New York",
    "state": "NY",
    "phone": "914-003-1132",
    "website": "https://www.theduelingpianos.com",
    "facebook_link": "https://www.facebook.com/theduelingpianos",
    "seeking_talent": False,
    "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": 0,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 3,
    "name": "Park Square Live Music & Coffee",
    "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    "address": "34 Whiskey Moore Ave",
    "city": "San Francisco",
    "state": "CA",
    "phone": "415-000-1234",
    "website": "https://www.parksquarelivemusicandcoffee.com",
    "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    "seeking_talent": False,
    "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    "past_shows": [{
      "artist_id": 5,
      "artist_name": "Matt Quevedo",
      "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [{
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 1,
    "upcoming_shows_count": 1,
  }
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=venueById)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  try: 
    form = request.form
    venue = Venue(
            name=form['name'],
            city=form['city'],
            state=form['state'],
            address=form['address'],
            phone=form['phone'],
            image_link=form['image_link'],
            facebook_link=form['facebook_link'],
            genres=form.getlist('genres'),   # if multiple checkbox
            seeking_description=form.get('seeking_description'),
            seeking_talent=form.get('seeking_talent') == 'y',
            website_link=form.get('website_link')
      )
    with app.app_context(): 
        db.session.add(venue)
        db.session.commit()
    flash('Venue ' + form['name'] + ' was successfully listed!')
  except Exception as e:
     db.session.rollback()
     flash('Venue ' + form['name'] + ' could not be listed.')
  finally:
     db.session.close()

  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  if not venue_id:
      return jsonify({"success": False, "error": "Not found"}), 404
  try:
     sql = f"""Delete from "Venue" v where v.id={venue_id}"""
     db.session.execute(sql)
     db.session.commit()
     flash('Venue deleted successfully!')
     return jsonify({"success": True})
  except:
     db.session.rollback()
     flash('Venue not deleted!')
     return jsonify({"success": False, "error": str(e)}), 500
  finally:
     db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(data={
    "name": venue.name,
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "genres": venue.genres,
    "image_link": venue.image_link,
    "facebook_link": venue.facebook_link,
    "website_link": venue.website_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description
  })
  # venue={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  # }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    form = request.form
    venue = Venue.query.get(venue_id)

    venue.name = form['name']
    venue.city = form['city']
    venue.state = form['state']
    venue.address = form['address']
    venue.phone = form['phone']
    venue.genres = ",".join(form.getlist('genres'))  # multi-select checkboxes
    venue.image_link = form.get('image_link')
    venue.facebook_link = form.get('facebook_link')
    venue.website_link = form.get('website_link')
    venue.seeking_talent = (form.get('seeking_talent') == 'y')
    venue.seeking_description = form.get('seeking_description')
    with app.app_context(): 
      db.session.commit()
  except Exception as e:
     db.session.rollback()
  finally:
     db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))