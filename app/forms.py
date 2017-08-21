from flask_wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

class LoginForm(Form):
    username = StringField('username', validators = [DataRequired()])
    password = StringField('password', validators = [DataRequired()])
    remember_me = BooleanField('remember_me', default = False)
    
class CreateNewAccountForm(Form):
    username = StringField('username', validators = [DataRequired()])
    password = StringField('password', validators = [DataRequired()])
    
class EventForm(Form):
    title = StringField('title', validators = [DataRequired()])
    date = StringField('date', validators = [DataRequired()])
    time = StringField('time', validators = [DataRequired()])
    description = StringField('description', validators = [DataRequired()])
    recipient = StringField('recipient')