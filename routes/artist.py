from extensions import db
from models import Artist, Show, Venue
from dateutil import parser
from flask import Blueprint, render_template, request, flash, redirect, url_for
from forms import *
from datetime import datetime
from sqlalchemy import func

artist_bp = Blueprint("artist", __name__, url_prefix='/artists')

#  Create Artist
#  ----------------------------------------------------------------
@artist_bp.route("/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@artist_bp.route("/create", methods=["POST"])
def create_artist_submission():
    try:
        form = request.form
        artist = Artist(
            name=form["name"],
            city=form["city"],
            state=form["state"],
            phone=form["phone"],
            image_link=form.get("image_link"),
            facebook_link=form.get("facebook_link"),
            genres=form.getlist("genres"),  # store as comma-separated string
            seeking_description=form.get("seeking_description"),
            seeking_venue=(form.get("seeking_venue") == "y"),
            website_link=form.get("website_link"),
        )

        # with app.app_context():
        db.session.add(artist)
        db.session.commit()
        flash("Artist " + form["name"] + " was successfully listed!")
    except Exception as e:
        db.session.rollback()
        flash("Artist " + form["name"] + " could not be listed.")
        print(e)
    finally:
        db.session.close()

    return render_template("pages/home.html")


#  Artists
#  ----------------------------------------------------------------
@artist_bp.route("/")
def artists():
    results = Artist.query.with_entities(Artist.id, Artist.name).order_by("id").all()
    data = [{"id": r.id, "name": r.name} for r in results]
    return render_template("pages/artists.html", artists=data)


@artist_bp.route("/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "")
    result = (
        db.session.query(
            Artist.id.label("id"),
            Artist.name.label("name"),
            func.count(Show.artist_id).label("num_upcoming_shows"),
        )
        .outerjoin(Show, Artist.id == Show.artist_id)  # LEFT JOIN
        .filter(func.lower(Artist.name).like(f"%{search_term.lower()}%"))
        .group_by(Artist.id)
        .all()
    )
    data = []
    for row in result:
        venue = {
            "id": row.id,
            "name": row.name,
            "num_upcoming_shows": row.num_upcoming_shows,
        }
        data.append(venue)

    response = {"count": len(result), "data": data}
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@artist_bp.route("/<int:artist_id>")
def show_artist(artist_id):
    artist_with_shows = (
        db.session.query(
            Artist,
            func.coalesce(
                func.json_agg(
                    func.json_build_object(
                        "venue_id",
                        Venue.id,
                        "venue_name",
                        Venue.name,
                        "venue_image_link",
                        Venue.image_link,
                        "start_time",
                        Show.start_time,
                    )
                ).filter(
                    Venue.id != None
                ),  # FILTER (WHERE v.id IS NOT NULL)
                func.cast("[]", db.JSON),  # default empty JSON array
            ).label("shows"),
        )
        .outerjoin(Show, Artist.id == Show.artist_id)
        .outerjoin(Venue, Show.venue_id == Venue.id)
        .filter(Artist.id == artist_id)
        .group_by(Artist.id)
        .first()
    )

    artistById = {}
    if artist_with_shows:
        artist, shows = artist_with_shows
        artistById = {
            "id": artist.id,
            "name": artist.name,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "genres": artist.genres,
            "image_link": artist.image_link,
            "facebook_link": artist.facebook_link,
            "website_link": artist.website_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "shows": shows,  # already a list of dicts from json_agg
        }
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

    return render_template("pages/show_artist.html", artist=artistById)


#  Update
#  ----------------------------------------------------------------
@artist_bp.route("/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(
        data={
            "name": artist.name,
            "genres": artist.genres,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website_link": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
        }
    )

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@artist_bp.route("/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    try:
        form = request.form
        artist = Artist.query.get(artist_id)
        artist.name = form["name"]
        artist.city = form["city"]
        artist.state = form["state"]
        artist.phone = form["phone"]
        artist.genres = ",".join(form.getlist("genres"))
        artist.image_link = form.get("image_link")
        artist.facebook_link = form.get("facebook_link")
        artist.website_link = form.get("website_link")
        artist.seeking_venue = form.get("seeking_venue") == "y"
        artist.seeking_description = form.get("seeking_description")
        # with app.app_context():
        db.session.commit()

    except Exception as e:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))
