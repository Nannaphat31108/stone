from datetime import datetime

from models import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=False
    )

    approved = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Review {self.name}>"