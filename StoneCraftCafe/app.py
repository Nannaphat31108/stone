import os
from datetime import datetime
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)

from config import Config
from models import db
from models.gallery import Gallery
from models.menu import MenuItem
from models.reservation import Reservation
from models.review import Review
from models.setting import RestaurantSetting
from models.user import User
from models.workshop import Workshop
from storage import delete_image, save_image


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "กรุณาเข้าสู่ระบบก่อน"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None

BASE_DIR = Path(__file__).resolve().parent

MENU_UPLOAD_FOLDER = BASE_DIR / "uploads" / "menu"
GALLERY_UPLOAD_FOLDER = BASE_DIR / "uploads" / "gallery"
WORKSHOP_UPLOAD_FOLDER = BASE_DIR / "uploads" / "workshop"


def clean_map_embed_url(value):
    """Accept a Google Maps embed URL or pasted iframe code and return a safe URL."""
    value = (value or "").strip()
    if not value:
        return ""
    if "<iframe" in value.lower():
        import re
        match = re.search(r'src=["\']([^"\']+)["\']', value, re.IGNORECASE)
        value = match.group(1).strip() if match else ""
    parsed = urlparse(value)
    allowed_hosts = {"www.google.com", "google.com", "maps.google.com"}
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts or "/maps/embed" not in parsed.path:
        return None
    return value



def image_url(value, image_type="menu"):
    """Return a Cloudinary URL or a local development upload URL."""
    if not value:
        return None
    if value.startswith(("https://", "http://")):
        return value
    endpoint = {
        "gallery": "uploaded_gallery_image",
        "workshop": "uploaded_workshop_image",
    }.get(image_type, "uploaded_menu_image")
    return url_for(endpoint, filename=value)


def get_restaurant_setting():
    setting = RestaurantSetting.query.first()

    if setting is None:
        setting = RestaurantSetting()
        db.session.add(setting)
        db.session.commit()

    return setting


@app.context_processor
def inject_restaurant_setting():
    return {
        "restaurant_setting": get_restaurant_setting(),
        "image_url": image_url
    }


@app.after_request
def disable_html_cache(response):
    """Ensure public/admin HTML reflects database changes immediately."""
    if response.mimetype == "text/html":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# =====================================
# Public routes
# =====================================

@app.route("/")
def home():
    featured_menu = (
        MenuItem.query
        .filter_by(available=True)
        .order_by(MenuItem.id.desc())
        .limit(3)
        .all()
    )

    gallery_items = (
        Gallery.query
        .order_by(Gallery.id.desc())
        .limit(4)
        .all()
    )

    return render_template(
        "index.html",
        featured_menu=featured_menu,
        gallery_items=gallery_items
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/menu")
def menu():
    menu_items = (
        MenuItem.query
        .filter_by(available=True)
        .order_by(
            MenuItem.category.asc(),
            MenuItem.id.desc()
        )
        .all()
    )

    return render_template(
        "menu.html",
        menu_items=menu_items
    )


@app.route("/gallery")
def gallery():
    gallery_items = (
        Gallery.query
        .order_by(Gallery.id.desc())
        .all()
    )

    return render_template(
        "gallery.html",
        gallery_items=gallery_items
    )


@app.route("/workshops")
def workshops():
    workshop_items = (
        Workshop.query
        .filter_by(published=True)
        .order_by(Workshop.featured.desc(), Workshop.event_date.asc(), Workshop.id.desc())
        .all()
    )
    return render_template("workshops.html", workshop_items=workshop_items)


@app.route("/workshops/<int:workshop_id>")
def workshop_detail(workshop_id):
    workshop = db.get_or_404(Workshop, workshop_id)
    if not workshop.published and not current_user.is_authenticated:
        abort(404)
    return render_template("workshop_detail.html", workshop=workshop)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route(
    "/reservation",
    methods=["GET", "POST"]
)
def reservation():
    if request.method == "POST":
        try:
            fullname = request.form.get(
                "fullname",
                ""
            ).strip()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            guests = int(
                request.form.get("guests", "0")
            )

            reserve_date = datetime.strptime(
                request.form.get("date", ""),
                "%Y-%m-%d"
            ).date()

            reserve_time = request.form.get(
                "time",
                ""
            ).strip()

            note = request.form.get(
                "note",
                ""
            ).strip()

            if not fullname or not phone:
                raise ValueError(
                    "กรุณากรอกชื่อและเบอร์โทร"
                )

            if guests < 1 or guests > 20:
                raise ValueError(
                    "จำนวนผู้ใช้บริการต้องอยู่ระหว่าง 1–20 คน"
                )

            if reserve_date < datetime.now().date():
                raise ValueError(
                    "ไม่สามารถเลือกวันที่ย้อนหลังได้"
                )

            new_reservation = Reservation(
                fullname=fullname,
                phone=phone,
                email=email,
                guests=guests,
                reserve_date=reserve_date,
                reserve_time=reserve_time,
                note=note,
                status="Pending"
            )

            db.session.add(new_reservation)
            db.session.commit()

            flash(
                "ส่งข้อมูลการจองเรียบร้อยแล้ว",
                "success"
            )

            return redirect(
                url_for("reservation")
            )

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")

        except Exception:
            db.session.rollback()
            app.logger.exception(
                "Reservation error"
            )

            flash(
                "ไม่สามารถบันทึกการจองได้",
                "error"
            )

    return render_template(
        "reservation.html"
    )


@app.route(
    "/review",
    methods=["GET", "POST"]
)
def review():
    if request.method == "POST":
        try:
            name = request.form.get(
                "name",
                ""
            ).strip()

            comment = request.form.get(
                "comment",
                ""
            ).strip()

            rating = int(
                request.form.get("rating", "0")
            )

            if not name or not comment:
                raise ValueError(
                    "กรุณากรอกชื่อและความคิดเห็น"
                )

            if rating not in range(1, 6):
                raise ValueError(
                    "คะแนนต้องอยู่ระหว่าง 1–5"
                )

            new_review = Review(
                name=name,
                rating=rating,
                comment=comment,
                approved=False
            )

            db.session.add(new_review)
            db.session.commit()

            flash(
                "ส่งรีวิวแล้ว รอผู้ดูแลตรวจสอบ",
                "success"
            )

            return redirect(
                url_for("review")
            )

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")

    reviews = (
        Review.query
        .filter_by(approved=True)
        .order_by(Review.id.desc())
        .all()
    )

    return render_template(
        "review.html",
        reviews=reviews
    )


@app.route("/uploads/menu/<filename>")
def uploaded_menu_image(filename):
    return send_from_directory(
        MENU_UPLOAD_FOLDER,
        filename
    )


@app.route("/uploads/gallery/<filename>")
def uploaded_gallery_image(filename):
    return send_from_directory(
        GALLERY_UPLOAD_FOLDER,
        filename
    )


@app.route("/uploads/workshop/<filename>")
def uploaded_workshop_image(filename):
    return send_from_directory(WORKSHOP_UPLOAD_FOLDER, filename)


# =====================================
# Admin authentication
# =====================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():
    if current_user.is_authenticated:
        return redirect(
            url_for("admin_dashboard")
        )

    if request.method == "POST":
        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and user.check_password(password):
            login_user(user)

            flash(
                "เข้าสู่ระบบสำเร็จ",
                "success"
            )

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
            "error"
        )

    return render_template(
        "admin/login.html"
    )


@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()

    flash(
        "ออกจากระบบแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_login")
    )


# =====================================
# Admin dashboard
# =====================================

@app.route("/admin")
@login_required
def admin_dashboard():
    statistics = {
        "menu_count": MenuItem.query.count(),
        "reservation_count": (
            Reservation.query.count()
        ),
        "pending_count": (
            Reservation.query
            .filter_by(status="Pending")
            .count()
        ),
        "review_count": Review.query.count(),
        "unapproved_review_count": (
            Review.query
            .filter_by(approved=False)
            .count()
        ),
        "gallery_count": Gallery.query.count()
    }

    latest_reservations = (
        Reservation.query
        .order_by(Reservation.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        statistics=statistics,
        latest_reservations=latest_reservations
    )


# =====================================
# Admin menu management
# =====================================

@app.route("/admin/menu")
@login_required
def admin_menu():
    menu_items = (
        MenuItem.query
        .order_by(MenuItem.id.desc())
        .all()
    )

    return render_template(
        "admin/menu_list.html",
        menu_items=menu_items
    )


@app.route(
    "/admin/menu/add",
    methods=["GET", "POST"]
)
@login_required
def admin_menu_add():
    if request.method == "POST":
        try:
            image_name = save_image(
                request.files.get("image"),
                MENU_UPLOAD_FOLDER,
                "menu"
            )

            item = MenuItem(
                name_th=request.form.get(
                    "name_th",
                    ""
                ).strip(),
                name_en=request.form.get(
                    "name_en",
                    ""
                ).strip(),
                category=request.form.get(
                    "category",
                    ""
                ).strip(),
                description_th=request.form.get(
                    "description_th",
                    ""
                ).strip(),
                description_en=request.form.get(
                    "description_en",
                    ""
                ).strip(),
                price=float(
                    request.form.get("price", "0")
                ),
                image=image_name,
                available=(
                    request.form.get("available")
                    == "on"
                )
            )

            if not item.name_th or not item.name_en:
                raise ValueError(
                    "กรุณากรอกชื่อเมนู"
                )

            db.session.add(item)
            db.session.commit()

            flash(
                "เพิ่มเมนูเรียบร้อยแล้ว",
                "success"
            )

            return redirect(
                url_for("admin_menu")
            )

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")

        except Exception:
            db.session.rollback()
            app.logger.exception(
                "Add menu error"
            )

            flash(
                "ไม่สามารถเพิ่มเมนูได้",
                "error"
            )

    return render_template(
        "admin/menu_form.html",
        item=None
    )


@app.route(
    "/admin/menu/<int:item_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def admin_menu_edit(item_id):
    item = db.get_or_404(
        MenuItem,
        item_id
    )

    if request.method == "POST":
        try:
            uploaded_file = request.files.get(
                "image"
            )

            if uploaded_file and uploaded_file.filename:
                new_image = save_image(
                    uploaded_file,
                    MENU_UPLOAD_FOLDER,
                    "menu"
                )

                delete_image(
                    item.image,
                    MENU_UPLOAD_FOLDER
                )

                item.image = new_image

            item.name_th = request.form.get(
                "name_th",
                ""
            ).strip()

            item.name_en = request.form.get(
                "name_en",
                ""
            ).strip()

            item.category = request.form.get(
                "category",
                ""
            ).strip()

            item.description_th = request.form.get(
                "description_th",
                ""
            ).strip()

            item.description_en = request.form.get(
                "description_en",
                ""
            ).strip()

            item.price = float(
                request.form.get("price", "0")
            )

            item.available = (
                request.form.get("available")
                == "on"
            )

            db.session.commit()

            flash(
                "แก้ไขเมนูเรียบร้อยแล้ว",
                "success"
            )

            return redirect(
                url_for("admin_menu")
            )

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")

    return render_template(
        "admin/menu_form.html",
        item=item
    )


@app.post("/admin/menu/<int:item_id>/delete")
@login_required
def admin_menu_delete(item_id):
    item = db.get_or_404(
        MenuItem,
        item_id
    )

    delete_image(
        item.image,
        MENU_UPLOAD_FOLDER
    )

    db.session.delete(item)
    db.session.commit()

    flash(
        "ลบเมนูเรียบร้อยแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_menu")
    )


# =====================================
# Reservation management
# =====================================

@app.route("/admin/reservations")
@login_required
def admin_reservations():
    reservations = (
        Reservation.query
        .order_by(Reservation.id.desc())
        .all()
    )

    return render_template(
        "admin/reservations.html",
        reservations=reservations
    )


@app.post(
    "/admin/reservations/<int:reservation_id>/status"
)
@login_required
def admin_reservation_status(reservation_id):
    booking = db.get_or_404(
        Reservation,
        reservation_id
    )

    status = request.form.get(
        "status",
        ""
    )

    allowed_statuses = {
        "Pending",
        "Confirmed",
        "Cancelled"
    }

    if status not in allowed_statuses:
        abort(400)

    booking.status = status
    db.session.commit()

    flash(
        "อัปเดตสถานะการจองแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_reservations")
    )


@app.post(
    "/admin/reservations/<int:reservation_id>/delete"
)
@login_required
def admin_reservation_delete(reservation_id):
    booking = db.get_or_404(
        Reservation,
        reservation_id
    )

    db.session.delete(booking)
    db.session.commit()

    flash(
        "ลบข้อมูลการจองแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_reservations")
    )


# =====================================
# Review management
# =====================================

@app.route("/admin/reviews")
@login_required
def admin_reviews():
    reviews = (
        Review.query
        .order_by(Review.id.desc())
        .all()
    )

    return render_template(
        "admin/reviews.html",
        reviews=reviews
    )


@app.post("/admin/reviews/<int:review_id>/approve")
@login_required
def admin_review_approve(review_id):
    review_item = db.get_or_404(
        Review,
        review_id
    )

    review_item.approved = not review_item.approved
    db.session.commit()

    flash(
        "อัปเดตสถานะรีวิวแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_reviews")
    )


@app.post("/admin/reviews/<int:review_id>/delete")
@login_required
def admin_review_delete(review_id):
    review_item = db.get_or_404(
        Review,
        review_id
    )

    db.session.delete(review_item)
    db.session.commit()

    flash(
        "ลบรีวิวแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_reviews")
    )


# =====================================
# Gallery management
# =====================================

@app.route(
    "/admin/gallery",
    methods=["GET", "POST"]
)
@login_required
def admin_gallery():
    if request.method == "POST":
        try:
            image_name = save_image(
                request.files.get("image"),
                GALLERY_UPLOAD_FOLDER,
                "gallery"
            )

            if image_name is None:
                raise ValueError(
                    "กรุณาเลือกรูปภาพ"
                )

            gallery_item = Gallery(
                title_th=request.form.get(
                    "title_th",
                    ""
                ).strip(),
                title_en=request.form.get(
                    "title_en",
                    ""
                ).strip(),
                image=image_name
            )

            db.session.add(gallery_item)
            db.session.commit()

            flash(
                "เพิ่มรูปแกลเลอรีแล้ว",
                "success"
            )

            return redirect(
                url_for("admin_gallery")
            )

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")

    gallery_items = (
        Gallery.query
        .order_by(Gallery.id.desc())
        .all()
    )

    return render_template(
        "admin/gallery.html",
        gallery_items=gallery_items
    )


@app.post("/admin/gallery/<int:gallery_id>/delete")
@login_required
def admin_gallery_delete(gallery_id):
    gallery_item = db.get_or_404(
        Gallery,
        gallery_id
    )

    delete_image(
        gallery_item.image,
        GALLERY_UPLOAD_FOLDER
    )

    db.session.delete(gallery_item)
    db.session.commit()

    flash(
        "ลบรูปแกลเลอรีแล้ว",
        "success"
    )

    return redirect(
        url_for("admin_gallery")
    )


# =====================================
# Workshop management
# =====================================

@app.route("/admin/workshops")
@login_required
def admin_workshops():
    workshop_items = Workshop.query.order_by(Workshop.id.desc()).all()
    return render_template("admin/workshop_list.html", workshop_items=workshop_items)


@app.route("/admin/workshops/add", methods=["GET", "POST"])
@login_required
def admin_workshop_add():
    if request.method == "POST":
        try:
            image_name = save_image(request.files.get("image"), WORKSHOP_UPLOAD_FOLDER, "workshop")
            event_date_value = request.form.get("event_date", "").strip()
            item = Workshop(
                title_th=request.form.get("title_th", "").strip(),
                title_en=request.form.get("title_en", "").strip(),
                short_description_th=request.form.get("short_description_th", "").strip(),
                short_description_en=request.form.get("short_description_en", "").strip(),
                details_th=request.form.get("details_th", "").strip(),
                details_en=request.form.get("details_en", "").strip(),
                event_date=datetime.strptime(event_date_value, "%Y-%m-%d").date() if event_date_value else None,
                start_time=request.form.get("start_time", "").strip(),
                end_time=request.form.get("end_time", "").strip(),
                location_th=request.form.get("location_th", "").strip(),
                location_en=request.form.get("location_en", "").strip(),
                price=float(request.form.get("price") or 0),
                capacity=int(request.form.get("capacity") or 0),
                booking_url=request.form.get("booking_url", "").strip(),
                image=image_name,
                published=request.form.get("published") == "on",
                featured=request.form.get("featured") == "on",
            )
            if not item.title_th or not item.title_en:
                raise ValueError("กรุณากรอกชื่อกิจกรรมทั้งภาษาไทยและอังกฤษ")
            db.session.add(item)
            db.session.commit()
            flash("เพิ่ม Workshop เรียบร้อยแล้ว", "success")
            return redirect(url_for("admin_workshops"))
        except Exception as error:
            db.session.rollback()
            app.logger.exception("Add workshop error")
            flash(f"เพิ่ม Workshop ไม่สำเร็จ: {error}", "error")
    return render_template("admin/workshop_form.html", item=None)


@app.route("/admin/workshops/<int:workshop_id>/edit", methods=["GET", "POST"])
@login_required
def admin_workshop_edit(workshop_id):
    item = db.get_or_404(Workshop, workshop_id)
    if request.method == "POST":
        try:
            new_image = request.files.get("image")
            if new_image and new_image.filename:
                delete_image(item.image, WORKSHOP_UPLOAD_FOLDER)
                item.image = save_image(new_image, WORKSHOP_UPLOAD_FOLDER, "workshop")
            event_date_value = request.form.get("event_date", "").strip()
            item.title_th = request.form.get("title_th", "").strip()
            item.title_en = request.form.get("title_en", "").strip()
            item.short_description_th = request.form.get("short_description_th", "").strip()
            item.short_description_en = request.form.get("short_description_en", "").strip()
            item.details_th = request.form.get("details_th", "").strip()
            item.details_en = request.form.get("details_en", "").strip()
            item.event_date = datetime.strptime(event_date_value, "%Y-%m-%d").date() if event_date_value else None
            item.start_time = request.form.get("start_time", "").strip()
            item.end_time = request.form.get("end_time", "").strip()
            item.location_th = request.form.get("location_th", "").strip()
            item.location_en = request.form.get("location_en", "").strip()
            item.price = float(request.form.get("price") or 0)
            item.capacity = int(request.form.get("capacity") or 0)
            item.booking_url = request.form.get("booking_url", "").strip()
            item.published = request.form.get("published") == "on"
            item.featured = request.form.get("featured") == "on"
            if not item.title_th or not item.title_en:
                raise ValueError("กรุณากรอกชื่อกิจกรรมทั้งภาษาไทยและอังกฤษ")
            db.session.commit()
            flash("บันทึก Workshop แล้ว", "success")
            return redirect(url_for("admin_workshops"))
        except Exception as error:
            db.session.rollback()
            app.logger.exception("Edit workshop error")
            flash(f"แก้ไข Workshop ไม่สำเร็จ: {error}", "error")
    return render_template("admin/workshop_form.html", item=item)


@app.route("/admin/workshops/<int:workshop_id>/delete", methods=["POST"])
@login_required
def admin_workshop_delete(workshop_id):
    item = db.get_or_404(Workshop, workshop_id)
    delete_image(item.image, WORKSHOP_UPLOAD_FOLDER)
    db.session.delete(item)
    db.session.commit()
    flash("ลบ Workshop แล้ว", "success")
    return redirect(url_for("admin_workshops"))


# =====================================
# Restaurant settings
# =====================================

@app.route(
    "/admin/settings",
    methods=["GET", "POST"]
)
@login_required
def admin_settings():
    setting = get_restaurant_setting()

    if request.method == "POST":
        setting.restaurant_name = request.form.get(
            "restaurant_name",
            ""
        ).strip()

        setting.phone = request.form.get(
            "phone",
            ""
        ).strip()

        setting.email = request.form.get(
            "email",
            ""
        ).strip()

        setting.address_th = request.form.get(
            "address_th",
            ""
        ).strip()

        setting.address_en = request.form.get(
            "address_en",
            ""
        ).strip()

        setting.facebook_url = request.form.get(
            "facebook_url",
            ""
        ).strip()

        setting.instagram_url = request.form.get(
            "instagram_url",
            ""
        ).strip()

        setting.tiktok_url = request.form.get(
            "tiktok_url",
            ""
        ).strip()

        setting.line_url = request.form.get(
            "line_url",
            ""
        ).strip()

        setting.grab_url = request.form.get(
            "grab_url",
            ""
        ).strip()

        raw_map_embed_url = request.form.get("map_embed_url", "")
        cleaned_map_embed_url = clean_map_embed_url(raw_map_embed_url)
        if raw_map_embed_url.strip() and cleaned_map_embed_url is None:
            flash("Embed URL ไม่ถูกต้อง กรุณาคัดลอกจาก Google Maps → Share → Embed a map", "error")
            return render_template("admin/settings.html", setting=setting), 400
        setting.map_embed_url = cleaned_map_embed_url or ""

        setting.map_url = request.form.get(
            "map_url",
            ""
        ).strip()

        db.session.commit()

        flash(
            "บันทึกข้อมูลร้านเรียบร้อยแล้ว",
            "success"
        )

        return redirect(
            url_for("admin_settings")
        )

    return render_template(
        "admin/settings.html",
        setting=setting
    )


# =====================================
# Application initialization
# =====================================

def initialize_database():
    with app.app_context():
        db.create_all()

        # Add newly introduced settings columns to existing databases.
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        setting_columns = {column["name"] for column in inspector.get_columns("restaurant_settings")}
        for column_name, column_type in (("map_embed_url", "TEXT"), ("map_url", "VARCHAR(1000)")):
            if column_name not in setting_columns:
                db.session.execute(text(f"ALTER TABLE restaurant_settings ADD COLUMN {column_name} {column_type}"))
        db.session.commit()

        admin = User.query.filter_by(
            username="admin"
        ).first()

        if admin is None:
            admin = User(
                username="admin",
                fullname="Administrator",
                role="admin"
            )

            admin.set_password(
                os.environ.get(
                    "ADMIN_PASSWORD",
                    "admin1234"
                )
            )

            db.session.add(admin)
            db.session.commit()

            print(
                "Created administrator account."
            )


# Gunicorn imports this module, so initialize tables/admin at startup too.
initialize_database()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")