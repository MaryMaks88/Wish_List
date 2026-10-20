import secrets
import os
import smtplib
from dotenv import load_dotenv
from email.message import EmailMessage
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Boolean, Text, Column, Date
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LogInForm, NewEvent, AddGift, EditEvent, EditGift
from flask_wtf.csrf import CSRFProtect

load_dotenv()

APP_PASS = os.environ.get("app_password")
MY_EMAIL = os.environ.get("my_email")
SECRET_KEY = os.environ.get("secret_key")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)



def send_notification_email(email, event, gift):

    msg = EmailMessage()
    msg["Subject"] = f"Subject: Gift reservation for {event.title}"
    msg["From"] = MY_EMAIL
    msg["To"] = email

    body = f"You have reserved a present: '{gift.title}'\n"
    if gift.link:
        body += f"Follow the link: {gift.link}\n"

    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", port=587, timeout=15) as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=APP_PASS)
        connection.send_message(msg=msg)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wishlist.db"
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(30), unique=True, nullable=False)
    password_hash = Column(String(250), nullable=False)
    events = db.relationship("Event", backref="owner", cascade="all, delete-orphan")

class Event(db.Model):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, db.ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=True)
    share_token = Column(String(32), unique=True, nullable=False,
                         default=lambda: secrets.token_urlsafe(16))
    items = db.relationship("Item", backref="event", cascade="all, delete-orphan")

class Item(db.Model):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, nullable=False)
    event_id = Column(Integer, db.ForeignKey("events.id"), nullable=False)
    title = Column(Text, nullable=False)
    link = Column(String(250), nullable=False)
    is_reserved = Column(Boolean, nullable=False, default=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    if current_user.is_authenticated:
        events = current_user.events
        return render_template("index.html", events=events)

    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user_exists = db.session.execute(db.select(User).where(User.name == form.name.data)).scalar()
        if user_exists:
            flash("Such name already exist. Pick another one. Or LogIn.")
            return redirect(url_for('register'))

        new_user = User(
            name=form.name.data,
            password_hash=generate_password_hash(form.password.data)
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LogInForm()
    if form.validate_on_submit():
        password = form.password.data
        name = form.name.data
        user = db.session.execute(db.select(User).where(User.name == name)).scalar_one_or_none()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Wrong name or password")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/new_event", methods=["POST", "GET"])
@login_required
def new_event():
    form = NewEvent()

    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            date=form.date.data,
            user_id=current_user.id
        )

        db.session.add(event)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("new_event.html", form=form)

@app.route("/add_gifts/<int:event_id>", methods=["POST", "GET"])
@login_required
def add_gifts(event_id):

    form = AddGift()

    if form.validate_on_submit():

        gift = Item(
            event_id=event_id,
            title=form.title.data,
            link=form.link.data
        )

        db.session.add(gift)
        db.session.commit()
        flash("Gift added")
        return redirect(url_for("add_gifts", event_id=event_id))

    gifts = db.session.execute(db.select(Item).where(Item.event_id == event_id)).scalars()
    event = db.session.execute(db.select(Event).where(Event.id == event_id)).scalar_one_or_none()
    share_url = url_for("guest_list", share_token=event.share_token, _external=True)

    return render_template("add_gifts.html", form=form, event=event, gifts=gifts, share_url=share_url)

@app.route("/guest_list/<share_token>")
def guest_list(share_token):
    event = Event.query.filter_by(share_token=share_token).first_or_404()
    return render_template("guest_list.html", event=event, gifts=event.items)


@app.route("/reservation/<share_token>/reserve/<int:gift_id>", methods=["POST"])
def reservation(share_token, gift_id):

    event = Event.query.filter_by(share_token=share_token).first_or_404()
    gift = Item.query.filter_by(id=gift_id, event_id=event.id).first_or_404()
    email = request.form.get("email", "").strip()

    if request.form.get("skip_email"):
        email = ""

    result = db.session.execute(db.update(Item)
                                .where(Item.id == gift_id, Item.is_reserved == False)
                                .values(is_reserved=True))
    db.session.commit()

    if result.rowcount == 0:
        flash("The gift is already reserved")
    else:
        flash("Thank you! The gift is reserved")
        if email:
            try:
                send_notification_email(email, event, gift)
                flash("Details have been sent to your email.")
            except Exception as e:
                app.logger.exception("Email failed")
                print("EMAIL ERROR:", repr(e))
                flash("Gift reserved, but the email couldn't be sent.")

    return redirect(url_for("guest_list", share_token=share_token))


@app.route("/edit_event/<int:event_id>", methods=["POST", "GET"])
@login_required
def edit_event(event_id):
    form = EditEvent()

    if form.validate_on_submit():
        event = Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
        title = form.title.data
        date = form.date.data
        if title:
            event.title = title
            db.session.commit()
        if date:
            event.date = date
            db.session.commit()

        flash("Event updated")
        return redirect(url_for("home"))

    return render_template("edit_event.html", form=form)

@app.route("/delete_event/<int:event_id>")
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted")
    return redirect(url_for("home"))

@app.route("/edit_gift/<int:gift_id>", methods=["GET", "POST"])
@login_required
def edit_gift(gift_id):

    form = EditGift()
    gift = db.session.execute(
        db.select(Item)
        .join(Event, Item.event_id == Event.id)
        .where(Item.id == gift_id, Event.user_id == current_user.id)
    ).scalar_one_or_none()

    if form.validate_on_submit():
        title = form.title.data
        link = form.link.data
        if title:
            gift.title = title
            db.session.commit()
        if link:
            gift.link = link
            db.session.commit()

        flash("Gift updated")
        return redirect(url_for("add_gifts", event_id=gift.event_id))

    return render_template("edit_gift.html", form=form, gift=gift)

@app.route("/delete_gift/<int:gift_id>")
@login_required
def delete_gift(gift_id):
    gift = db.session.execute(
        db.select(Item)
        .join(Event, Item.event_id == Event.id)
        .where(Item.id == gift_id, Event.user_id == current_user.id)
    ).scalar_one_or_none()
    db.session.delete(gift)
    db.session.commit()
    flash("Gift deleted")
    return redirect(url_for("add_gifts", event_id=gift.event_id))

if __name__ == "__main__":
    app.run(debug=True, port=5002)