from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class MetaCeleb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(10))
    name = db.Column(db.String(30), nullable=False)
    real_name = db.Column(db.String(30))
    job = db.Column(db.String(100))
    dob = db.Column(db.String(30))
    company = db.Column(db.String(100))  
    img = db.Column(db.Text, unique = True, nullable=False)
    img_name = db.Column(db.Text, nullable=False)
    img_mimetype = db.Column(db.Text, nullable=False)
    nationality = db.Column(db.String(30))
    keyword = db.Column(db.String(200))
    copyright_status = db.Column(db.String(50))
    date_pub = db.Column(db.String(10))
    monitored = db.Column(db.String(5))
    date_monitor = db.Column(db.String(10))
    suggested = db.Column(db.String(5))
    date_suggested = db.Column(db.String(10))
    story = db.Column(db.String(10000))
    feedback = db.Column(db.String(5000))
    date = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(10))  
    img = db.Column(db.Text, unique = True, nullable=False)
    img_name = db.Column(db.Text, nullable=False)
    img_mimetype = db.Column(db.Text, nullable=False)
    metaceleb_name = db.Column(db.Text)
    note = db.Column(db.String(2000))
    date = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'Pic Name: {self.name}'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    ips_metaceleb = db.relationship('MetaCeleb', backref = 'author', lazy = True)
