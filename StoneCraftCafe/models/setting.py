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

    opening_hours = db.Column(
        db.Text,
        nullable=True,
        default="เปิดทุกวัน 09:00–21:00"
    )

    parking_info = db.Column(
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

    # Existing database column names are preserved for compatibility.
    map_embed_url = db.Column(
        db.Text,
        nullable=True
    )

    map_url = db.Column(
        db.String(1000),
        nullable=True
    )

    @property
    def google_maps_embed(self):
        return self.map_embed_url or ""

    @google_maps_embed.setter
    def google_maps_embed(self, value):
        self.map_embed_url = value or ""

    @property
    def google_maps_url(self):
        return self.map_url or ""

    @google_maps_url.setter
    def google_maps_url(self, value):
        self.map_url = value or ""

    def __repr__(self):
        return (
            f"<RestaurantSetting id={self.id} "
            f"name={self.restaurant_name!r}>"
        )
