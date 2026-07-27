from datetime import datetime

from models import db


class Workshop(db.Model):
    __tablename__ = "workshops"

    id = db.Column(db.Integer, primary_key=True)

    title_th = db.Column(
        db.String(255),
        nullable=False,
    )
    title_en = db.Column(
        db.String(255),
        nullable=False,
    )

    description_th = db.Column(
        db.Text,
        nullable=True,
    )
    description_en = db.Column(
        db.Text,
        nullable=True,
    )

    event_date = db.Column(
        db.Date,
        nullable=True,
        index=True,
    )
    start_time = db.Column(
        db.String(20),
        nullable=True,
    )
    end_time = db.Column(
        db.String(20),
        nullable=True,
    )

    location_th = db.Column(
        db.String(255),
        nullable=True,
    )
    location_en = db.Column(
        db.String(255),
        nullable=True,
    )

    price = db.Column(
        db.Float,
        nullable=False,
        default=0,
    )
    capacity = db.Column(
        db.Integer,
        nullable=True,
    )

    image = db.Column(
        db.Text,
        nullable=True,
    )
    booking_url = db.Column(
        db.Text,
        nullable=True,
    )

    published = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return (
            f"<Workshop id={self.id} "
            f"title={self.title_en!r}>"
        )
