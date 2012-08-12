# -*- coding: utf-8 -*-

from flask.ext.wtf import Form, TextField, TextAreaField, PasswordField,\
        DateTimeField, SubmitField, SelectField, HiddenField, BooleanField, RecaptchaField
from flask.ext.wtf import Required, Length, EqualTo, Optional, NumberRange, Email,\
        ValidationError, URL
from flask.ext.wtf.html5 import IntegerField, EmailField
import re
from hashlib import sha512
from flamejam import app, models

############## VALIDATORS ####################

class Not(object):
    def __init__(self, call, message = None):
        self.call = call
        self.message = message

    def __call__(self, form, field):
        errored = False
        try:
            self.call(form, field)
        except ValidationError:
            # there was an error, so don't do anything
            errored = True

        if not errored:
            raise ValidationError(self.call.message if self.message == None else self.message)

class MatchesRegex(object):
    def __init__(self, regex, message = "This field matches the regex {0}"):
        self.regex = regex
        self.message = message

    def __call__(self, form, field):
        if re.search(self.regex, field.data):
            raise ValidationError(self.message.format(self.regex))

class UsernameExists(object):
    def __call__(self, form, field):
        u = models.User.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError("The username does not exist.")

class EmailExists(object):
    def __call__(self, form, field):
        e = models.User.query.filter_by(email = field.data).first()
        if not e:
            raise ValidationError("That email does not exist")

class LoginValidator(object):
    def __init__(self, pw_field, message_username = "The username or password is incorrect.", message_password = "The username or password is incorrect."):
        self.pw_field = pw_field
        self.message_username = message_username
        self.message_password = message_password

    def __call__(self, form, field):
        u = models.User.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError(self.message_username)
        elif u.password != sha512((form[self.pw_field].data+app.config['SECRET_KEY']).encode('utf-8')).hexdigest():
            raise ValidationError(self.message_password)

class UsernameValidator(object):
    def __init__(self, message_username = "The username is incorrect."):
        self.message_username = message_username

    def __call__(self, form, field):
        u = models.Participant.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError(self.message_username)

############## FORMS ####################

class UserLogin(Form):
    username = TextField("Username", validators=[LoginValidator("password")])
    password = PasswordField("Password", validators = [])

class UserRegistration(Form):
    username = TextField("Username", validators=[
        MatchesRegex("[^0-9a-zA-Z\-_]", "Your username contains invalid characters. Only use alphanumeric characters, dashes and underscores."),
        Not(UsernameExists(), message = "That username already exists."),
        Length(min=3, max=80, message="You have to enter a username of 3 to 80 characters length.")])
    password = PasswordField("Password", validators=[Length(min=8, message = "Please enter a password of at least 8 characters.")])
    password2 = PasswordField("Password, again", validators=[EqualTo("password", "Passwords do not match.")])
    email = EmailField("Email", validators=[
            Not(EmailExists(), message = "That email address is already in use."),
            Email(message = "The email address you entered is invalid.")])
    receive_emails = BooleanField("I want to receive email notifications.", default = True)
    captcha = RecaptchaField()

class ResetPassword(Form):
    username = TextField("Username", validators=[UsernameValidator()])

class NewPassword(Form):
    password = PasswordField("Password", validators=[Length(min=8, message = "Please enter a password of at least 8 characters.")])
    password2 = PasswordField("Password, again", validators=[EqualTo("password", "Passwords do not match.")])

class VerifyForm(Form):
    pass

class NewJam(Form):
    title = TextField("Jam title", validators=[Required(), Length(max=128)])
    theme = TextField("Theme", validators=[Required(), Length(max=128)])
    start_time = DateTimeField("Start time", format="%Y-%m-%d %H:%M", validators=[Required()])
    duration = IntegerField("Duration, in hours", validators=[NumberRange(min = 1), Required()], default = 48)
    team_jam = BooleanField("Team Jam", default = False)

class EditJam(Form):
    title = TextField("Jam title", validators=[Required(), Length(max=128)])
    theme = TextField("Theme", validators=[Required(), Length(max=128)])
    start_time = DateTimeField("Start time", format="%Y-%m-%d %H:%M", validators=[Required()])
    email = BooleanField("Send everyone an email about this change", default = True)

class SubmitEditGame(Form):
    title = TextField("Game title", validators=[Required(), Length(max=128)])
    description = TextAreaField("Description", validators=[Required()])

class GameAddScreenshot(Form):
    url = TextField("URL", validators = [Required(), URL()])
    caption = TextField("Caption", validators = [Required()])

class GameAddTeamMember(Form):
    username = TextField("Username:", validators = [Required(), UsernameExists()])

from models import game_package_type_string

class GameAddPackage(Form):
    url = TextField("URL", validators = [Required()])
    type = SelectField("Type", choices = [
        ("web",          game_package_type_string("web")),
        ("linux",        game_package_type_string("linux")),
        ("linux32",      game_package_type_string("linux32")),
        ("linux64",      game_package_type_string("linux64")),
        ("windows",      game_package_type_string("windows")),
        ("windows64",    game_package_type_string("windows64")),
        ("mac",          game_package_type_string("mac")),
        ("source",       game_package_type_string("source")),
        ("git",          game_package_type_string("git")),
        ("svn",          game_package_type_string("svn")),
        ("hg",           game_package_type_string("hg")),
        ("combi",        game_package_type_string("combi")),
        ("love",         game_package_type_string("love")),
        ("blender",      game_package_type_string("blender")),
        ("unknown",      game_package_type_string("unknown"))])

class RateGame(Form):
    game_id = HiddenField(validators = [Required(), NumberRange(min = 1)])
    score_gameplay = IntegerField("Gameplay rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_graphics = IntegerField("Graphics rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_audio = IntegerField("Audio rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_innovation = IntegerField("Innovation rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_story = IntegerField("Story rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_technical = IntegerField("Technical rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_controls = IntegerField("Controls rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_overall = IntegerField("Overall rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    note = TextField("Additional notes", validators=[Optional()])

class SkipRating(Form):
    game_id = HiddenField(validators = [Required(), NumberRange(min = 1)])
    reason = SelectField("Reason to skip", choices = [
        ("platform", "Platform not supported"),
        ("uninteresting", "Not interested"),
        ("crash", "Game crashed on start")
    ])

class WriteComment(Form):
    text = TextAreaField("Comment", validators=[Required(), Length(max=65535)])


class TeamFinderFilter(Form):
    need_programmer = BooleanField("Programmer")
    need_gamedesigner = BooleanField("Game Designer")
    need_2dartist = BooleanField("2D Artist")
    need_3dartist = BooleanField("3D Artist")
    need_composer = BooleanField("Composer")
    need_sounddesigner = BooleanField("Sound Designer")

    show_teamed = BooleanField("Show people with team")
    order = SelectField("Sort by", choices = [
        ("abilities", "Ability match"),
        ("username", "Username"),
        ("location", "Location")
    ], default = "abilities")
