from app import app, db
from models import Artist
from dateutil import parser
from flask import render_template, request, flash, redirect, url_for
from forms import *
from datetime import datetime

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
      form = request.form
      artist = Artist(
          name=form['name'],
          city=form['city'],
          state=form['state'],
          phone=form['phone'],
          image_link=form.get('image_link'),
          facebook_link=form.get('facebook_link'),
          genres=form.getlist('genres'),   # store as comma-separated string
          seeking_description=form.get('seeking_description'),
          seeking_venue=(form.get('seeking_venue') == 'y'),
          website_link=form.get('website_link')
      )

      with app.app_context():
          db.session.add(artist)
          db.session.commit()
      flash('Artist ' + form['name'] + ' was successfully listed!')
  except Exception as e:
      db.session.rollback()
      flash('Artist ' + form['name'] + ' could not be listed.')
      print(e)
  finally:
      db.session.close()

  return render_template('pages/home.html')



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  results = Artist.query.with_entities(Artist.id, Artist.name).order_by("id").all()
  data = [
    {"id": r.id, "name": r.name} 
    for r in results
  ]
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '') 
  sql = f"""select
          a.id,
          a.name,
          COUNT(s.artist_id) as num_upcoming_shows
        from
          "Artist" a
        left join "Show" s on
          a.id = s.artist_id
        where
          LOWER(name) like LOWER('%{search_term}%')
        group by
          a.id"""
  result = db.session.execute(sql).fetchall()

  # artistByName = db.session.execute(sql).fetchall()
  data = []
  for row in result:
     venue = {
        "id": row["id"],
        "name": row["name"],
        "num_upcoming_shows": row["num_upcoming_shows"]
     }
     data.append(venue)
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }

  response ={
     "count": len(result),
     "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  sql = f"""select
          a.*,
          coalesce(
                json_agg(
                  json_build_object(
                    'venue_id', v.id,
                    'venue_name', v.name,
                    'venue_image_link', v.image_link,
                    'start_time', s.start_time
                  )
                ) filter (where v.id is not null), -- avoid `[null]` when no artists
                '[]'::json
              ) as shows
        from
          "Artist" a
        left join "Show" s on
          a.id = s.artist_id
        left join "Venue" v on
          s.venue_id = v.id
        where a.id={artist_id}
        group by
          a.id"""

  result = db.session.execute(sql)
  columns = result.keys()
  list = [dict(zip(columns, row)) for row in result]
  artistById = list[0]

  upcoming_shows = []
  past_shows = []
  for show in artistById["shows"]:
    start_time = parser.parse(show["start_time"])
    now = datetime.now()
    if start_time > now:
       upcoming_shows.append(show)
    else:
       past_shows.append(show)
  artistById["upcoming_shows"] = upcoming_shows
  artistById["past_shows"] = past_shows
  artistById["upcoming_shows_count"] = len(upcoming_shows)
  artistById["past_shows_count"] = len(past_shows)
  del artistById["shows"]

  print_data("artistById ", artistById)
  data1={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "past_shows": [{
      "venue_id": 1,
      "venue_name": "The Musical Hop",
      "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data2={
    "id": 5,
    "name": "Matt Quevedo",
    "genres": ["Jazz"],
    "city": "New York",
    "state": "NY",
    "phone": "300-400-5000",
    "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "past_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 6,
    "name": "The Wild Sax Band",
    "genres": ["Jazz", "Classical"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "432-325-5432",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "past_shows": [],
    "upcoming_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 0,
    "upcoming_shows_count": 3,
  }
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=artistById)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  print_data("artist", artist)

  form = ArtistForm(data={
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  })
  
  # artist={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  # }

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    form = request.form
    artist = Artist.query.get(artist_id)
    artist.name = form['name']
    artist.city = form['city']
    artist.state = form['state']
    artist.phone = form['phone']
    artist.genres = ",".join(form.getlist('genres'))
    artist.image_link = form.get('image_link')
    artist.facebook_link = form.get('facebook_link')
    artist.website_link = form.get('website_link')
    artist.seeking_venue = (form.get('seeking_venue') == 'y')
    artist.seeking_description = form.get('seeking_description')
    with app.app_context(): 
      db.session.commit()
    
  except Exception as e:
     db.session.rollback()
  finally:
     db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))
