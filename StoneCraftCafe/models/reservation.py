from datetime import datetime

from models import db


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)

    fullname = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=True
    )

    guests = db.Column(
        db.Integer,
        nullable=False
    )

    reserve_date = db.Column(
        db.Date,
        nullable=False
    )

    reserve_time = db.Column(
        db.String(20),
        nullable=False
    )

    note = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Reservation {self.fullname}>"