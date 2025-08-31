from extensions import db

from models import Venue, Show, Artist

from dateutil import parser
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from forms import *
from datetime import datetime
from sqlalchemy import func

venue_bp = Blueprint("venue", __name__, url_prefix='/venues')

#  Venues
#  ----------------------------------------------------------------
@venue_bp.route("/")
def venues():
    venue_show_count = (
        db.session.query(
            Venue.id.label("id"), func.count(Show.venue_id).label("num_upcoming_shows")
        )
        .outerjoin(Show, Venue.id == Show.venue_id)
        .group_by(Venue.id)
        .all()
    )
    venue_show_map = {}
    for row in venue_show_count:
        venueId = row.id
        num_upcoming_shows = row.num_upcoming_shows
        venue_show_map[venueId] = num_upcoming_shows

    venuesByCityState = (
        db.session.query(
            Venue.city,
            Venue.state,
            func.json_agg(
                func.json_build_object("id", Venue.id, "name", Venue.name)
            ).label("venues"),
        )
        .group_by(Venue.city, Venue.state)
        .order_by(Venue.state, Venue.city)
        .all()
    )

    data = []
    for cityStateData in venuesByCityState:
        row = {}
        row["city"] = cityStateData.city
        row["state"] = cityStateData.state
        row["venues"] = []
        for venue in cityStateData.venues:
            venueItem = {}

            venue["new_upcoming_shows"] = venue_show_map.get(venue["id"], 0)
            venueItem["id"] = venue["id"]
            venueItem["name"] = venue["name"]
            venueItem["new_upcoming_shows"] = venue["new_upcoming_shows"]
            row["venues"].append(venueItem)
        data.append(row)

    return render_template("pages/venues.html", areas=data)


@venue_bp.route("/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "")
    venuesByName = (
        db.session.query(
            Venue.id, Venue.name, func.count(Show.venue_id).label("num_upcoming_shows")
        )
        .join(Show, Venue.id == Show.venue_id)
        .filter(Venue.name.ilike(f"%{search_term}%"))
        .group_by(Venue.id)
        .all()
    )

    data = []
    for row in venuesByName:
        venue = {
            "id": row.id,
            "name": row.name,
            "num_upcoming_shows": row.num_upcoming_shows,
        }
        data.append(venue)

    response = {"count": len(venuesByName), "data": data}

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@venue_bp.route("/<int:venue_id>")
def show_venue(venue_id):
    venue_with_shows = (
        db.session.query(
            Venue,
            func.coalesce(
                func.json_agg(
                    func.json_build_object(
                        "artist_id",
                        Artist.id,
                        "artist_name",
                        Artist.name,
                        "artist_image_link",
                        Artist.image_link,
                        "start_time",
                        Show.start_time,
                    )
                ).filter(
                    Artist.id != None
                ),  # same as FILTER (WHERE a.id IS NOT NULL)
                func.cast("[]", db.JSON),  # fallback [] instead of null
            ).label("shows"),
        )
        .outerjoin(Show, Venue.id == Show.venue_id)
        .outerjoin(Artist, Show.artist_id == Artist.id)
        .filter(Venue.id == venue_id)
        .group_by(Venue.id)
        .first()
    )
    venueById = {}
    if venue_with_shows:
        venue, shows = venue_with_shows
        venueById = {
            "id": venue.id,
            "name": venue.name,
            "city": venue.city,
            "state": venue.state,
            "address": getattr(venue, "address", None),  # if exists
            "phone": venue.phone,
            "image_link": venue.image_link,
            "facebook_link": venue.facebook_link,
            "website_link": venue.website_link,
            "seeking_talent": getattr(venue, "seeking_talent", False),
            "seeking_description": venue.seeking_description,
            "shows": shows,  # already a list of dicts from json_agg
        }

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

    return render_template("pages/show_venue.html", venue=venueById)


#  Create Venue
#  ----------------------------------------------------------------
@venue_bp.route("/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@venue_bp.route("/create", methods=["POST"])
def create_venue_submission():
    try:
        form = request.form
        venue = Venue(
            name=form["name"],
            city=form["city"],
            state=form["state"],
            address=form["address"],
            phone=form["phone"],
            image_link=form["image_link"],
            facebook_link=form["facebook_link"],
            genres=form.getlist("genres"),  # if multiple checkbox
            seeking_description=form.get("seeking_description"),
            seeking_talent=form.get("seeking_talent") == "y",
            website_link=form.get("website_link"),
        )
        # with app.app_context():
        db.session.add(venue)
        db.session.commit()
        flash("Venue " + form["name"] + " was successfully listed!")
    except Exception as e:
        db.session.rollback()
        flash("Venue " + form["name"] + " could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


@venue_bp.route("/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    if not venue_id:
        return jsonify({"success": False, "error": "Not found"}), 404
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue deleted successfully!")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        flash("Venue not deleted!")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.session.close()

#  Update Venue
#  ----------------------------------------------------------------
@venue_bp.route("/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(
        data={
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
            "seeking_description": venue.seeking_description,
        }
    )
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@venue_bp.route("/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    try:
        form = request.form
        venue = Venue.query.get(venue_id)

        venue.name = form["name"]
        venue.city = form["city"]
        venue.state = form["state"]
        venue.address = form["address"]
        venue.phone = form["phone"]
        venue.genres = ",".join(form.getlist("genres"))  # multi-select checkboxes
        venue.image_link = form.get("image_link")
        venue.facebook_link = form.get("facebook_link")
        venue.website_link = form.get("website_link")
        venue.seeking_talent = form.get("seeking_talent") == "y"
        venue.seeking_description = form.get("seeking_description")
        # with app.app_context():
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for("show_venue", venue_id=venue_id))
