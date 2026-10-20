from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField
from wtforms.validators import DataRequired, Optional

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class LogInForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LogIn")

class NewEvent(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    date = DateField("Date", validators=[Optional()])
    submit = SubmitField("Create event")

class EditEvent(FlaskForm):
    title = StringField("Title", validators=[Optional()])
    date = DateField("Date", validators=[Optional()])
    submit = SubmitField("Edit event")

class AddGift(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    link = StringField("Link", validators=[DataRequired()])
    submit = SubmitField("Add gift")

class EditGift(FlaskForm):
    title = StringField("Title", validators=[Optional()])
    link = StringField("Link", validators=[Optional()])
    submit = SubmitField("Edit gift")