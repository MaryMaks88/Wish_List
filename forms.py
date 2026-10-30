from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms import StringField, SubmitField, PasswordField, DateField
from wtforms.validators import DataRequired, Optional

class RegisterForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    submit = SubmitField(_l("Register"))

class LogInForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    submit = SubmitField(_l("LogIn"))

class NewEvent(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired()])
    date = DateField(_l("Date"), validators=[Optional()])
    submit = SubmitField(_l("Create event"))

class EditEvent(FlaskForm):
    title = StringField(_l("Title"), validators=[Optional()])
    date = DateField(_l("Date"), validators=[Optional()])
    submit = SubmitField(_l("Edit event"))

class AddGift(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired()])
    link = StringField(_l("Link"), validators=[DataRequired()])
    submit = SubmitField(_l("Add gift"))

class EditGift(FlaskForm):
    title = StringField(_l("Title"), validators=[Optional()])
    link = StringField(_l("Link"), validators=[Optional()])
    submit = SubmitField(_l("Edit gift"))