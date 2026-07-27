from models import db


class RestaurantSetting(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    restaurant_name = db.Column(
        db.String(255),
        nullable=False,
        default="Stone Craft Cafe & Bistro",
    )

    phone = db.Column(
        db.String(50),
        nullable=True,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    address_th = db.Column(
        db.Text,
        nullable=True,
    )

    address_en = db.Column(
        db.Text,
        nullable=True,
    )

    facebook_url = db.Column(
        db.Text,
        nullable=True,
    )

    instagram_url = db.Column(
        db.Text,
        nullable=True,
    )

    tiktok_url = db.Column(
        db.Text,
        nullable=True,
    )

    line_url = db.Column(
        db.Text,
        nullable=True,
    )

    grab_url = db.Column(
        db.Text,
        nullable=True,
    )

    # ลิงก์สำหรับกดเปิดแอปหรือหน้า Google Maps
    google_maps_url = db.Column(
        db.Text,
        nullable=True,
    )

    # รองรับทั้ง Embed URL และโค้ด iframe เต็ม
    google_maps_embed = db.Column(
        db.Text,
        nullable=True,
    )

    opening_hours = db.Column(
        db.Text,
        nullable=True,
    )

    parking_info = db.Column(
        db.Text,
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<RestaurantSetting "
            f"id={self.id} "
            f"name={self.restaurant_name!r}>"
        )