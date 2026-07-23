from models import db


class RestaurantSetting(db.Model):
    __tablename__ = "restaurant_settings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    restaurant_name = db.Column(
        db.String(150),
        nullable=False,
        default="Stone Craft Cafe & Bistro"
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    email = db.Column(
        db.String(120),
        nullable=True
    )

    address_th = db.Column(
        db.Text,
        nullable=True
    )

    address_en = db.Column(
        db.Text,
        nullable=True
    )

    facebook_url = db.Column(
        db.String(500),
        nullable=True
    )

    instagram_url = db.Column(
        db.String(500),
        nullable=True
    )

    tiktok_url = db.Column(
        db.String(500),
        nullable=True
    )

    line_url = db.Column(
        db.String(500),
        nullable=True
    )

    grab_url = db.Column(
        db.String(500),
        nullable=True
    )

    map_embed_url = db.Column(
        db.Text,
        nullable=True
    )

    map_url = db.Column(
        db.String(1000),
        nullable=True
    )

