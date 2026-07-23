import os
from datetime import datetime
from functools import wraps
from pathlib import Path

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
from storage import delete_image, save_image


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "กรุณาเข้าสู่ระบบก่อน"
login_manager.login_message_category = "warning"

BASE_DIR = Path(__file__).resolve().parent

MENU_UPLOAD_FOLDER = BASE_DIR / "uploads" / "menu"
GALLERY_UPLOAD_FOLDER = BASE_DIR / "uploads" / "gallery"



def image_url(value, image_type="menu"):
    """Return a Cloudinary URL or a local development upload URL."""
    if not value:
        return None
    if value.startswith(("https://", "http://")):
        return value
    endpoint = "uploaded_gallery_image" if image_type == "gallery" else "uploaded_menu_image"
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
# Restaurant settings
# =====================================

@app.route(
    "/admin/settings",
    methods=["GET", "POST"]
)
@admin_required
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
    app.run(debug=True)