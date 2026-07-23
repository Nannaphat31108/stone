from datetime import datetime

from models import db


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)

    name_th = db.Column(
        db.String(150),
        nullable=False
    )

    name_en = db.Column(
        db.String(150),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    description_th = db.Column(
        db.Text,
        nullable=True
    )

    description_en = db.Column(
        db.Text,
        nullable=True
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    image = db.Column(
        db.String(255),
        nullable=True
    )

    available = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )