from datetime import datetime

from models import db


class Workshop(db.Model):
    __tablename__ = "workshops"

    id = db.Column(db.Integer, primary_key=True)
    title_th = db.Column(db.String(180), nullable=False)
    title_en = db.Column(db.String(180), nullable=False)
    short_description_th = db.Column(db.Text, nullable=True)
    short_description_en = db.Column(db.Text, nullable=True)
    details_th = db.Column(db.Text, nullable=True)
    details_en = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.Date, nullable=True)
    start_time = db.Column(db.String(20), nullable=True)
    end_time = db.Column(db.String(20), nullable=True)
    location_th = db.Column(db.String(255), nullable=True)
    location_en = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    booking_url = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(500), nullable=True)
    published = db.Column(db.Boolean, nullable=False, default=True)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Workshop {self.title_en}>"
