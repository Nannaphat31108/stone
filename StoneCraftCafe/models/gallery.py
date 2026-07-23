from datetime import datetime

from models import db


class Gallery(db.Model):
    __tablename__ = "gallery"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title_th = db.Column(
        db.String(150),
        nullable=True
    )

    title_en = db.Column(
        db.String(150),
        nullable=True
    )

    image = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Gallery {self.id}>"