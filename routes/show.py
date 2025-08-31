from extensions import db

from models import Show

from flask import Blueprint, render_template, request, flash
from forms import *
from models import Venue, Artist, Show

show_bp = Blueprint("show", __name__, url_prefix='/shows')

#  Shows
#  ----------------------------------------------------------------
@show_bp.route("/")
def shows():
    result = (
        db.session.query(
            Venue.id.label("venue_id"),
            Venue.name.label("venue_name"),
            Artist.id.label("artist_id"),
            Artist.name.label("artist_name"),
            Artist.image_link.label("artist_image_link"),
            Show.start_time.label("start_time"),
        )
        .join(Show, Artist.id == Show.artist_id)
        .join(Venue, Venue.id == Show.venue_id)
        .all()
    )
    data = [
        {
            "venue_id": r.venue_id,
            "venue_name": r.venue_name,
            "artist_id": r.artist_id,
            "artist_name": r.artist_name,
            "artist_image_link": r.artist_image_link,
            "start_time": r.start_time,
        }
        for r in result
    ]
    return render_template("pages/shows.html", shows=data)

#  Create Shows
#  ----------------------------------------------------------------
@show_bp.route("/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@show_bp.route("/create", methods=["POST"])
def create_show_submission():
    try:
        form = request.form
        show = Show(
            artist_id=form["artist_id"],
            venue_id=form["venue_id"],
            start_time=form["start_time"],
        )

        # with app.app_context():
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except Exception as e:
        db.session.rollback()
        flash("Show was not listed!")
        print(e)
    finally:
        db.session.close()
    return render_template("pages/home.html")
