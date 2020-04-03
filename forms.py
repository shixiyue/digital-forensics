from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms.validators import DataRequired, Regexp

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), validators.Length(min=6, max=35)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SignupForm(FlaskForm): 
    email = StringField('Email', validators=[DataRequired(), Regexp(".*\.edu$", message="Must register with .edu email address")])
    password = PasswordField('Password', validators=[DataRequired(), validators.Length(min=6, max=35)])
    submit = SubmitField('Sign Up')