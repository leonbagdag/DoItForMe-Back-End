from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

user_category = db.Table('categories', db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    role = db.Column(db.String(10), default = 'user', nullable = False) # Role is user or admin
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(20), nullable = False)
    register_date = db.Column(db.DateTime, default = datetime.now)

    profile = db.relationship('Userprofile', backref='user', uselist=False, lazy=True) # 1 to 1 with profile
    reviews = db.relationship('Review', backref="user", lazy=True) # 1 to many with reviews
    categories = db.relationship('Category', secondary = user_category, back_populates = "users", lazy=True) #many to many with categories

    def __repr__(self):
        return '<User %r>' % self.username
    
    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
            "since": self.register_date.year
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    logo = db.Column(db.String(60), uniqye=True, nullable=False)

    users = db.relationship('User', secondary = user_category, back_populates = categories, lazy = True) #many to many with users

    def __repr__(self):
        return '<Category %r>' % self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo
        }


class Userprofile(db.Model): # Relación 1 a 1 con User
    id = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String(80))
    lname = db.Column(db.String(80))
    region = db.Column(db.String(80))
    comuna = db.Column(db.String(80))
    address_1 = db.Column(db.String(120))
    address_2 = db.Column(db.String(120))
    rut = db.Column(db.String(10))
    rut_serial = db.Column(db.String(20))
    score_as_provider = db.Column(db.Float, default = 0)
    score_as_employer = db.Column(db.Float, default = 0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Profile %r>' % self.fname
    
    def serialize(self):
        return {
            "firstName": self.fname,
            "lastName": self.lname,
            "region": self.region,
            "comuna": self.comuna,
            "address1": self.address_1,
            "address2": self.address_2,
            "score_as_provider": self.score_as_provider,
            "score_as_employer": self.score_as_employer
        }

class Review(db.Model): #Relación 1 a muchos con User
    id = db.Column(db.Integer, primary_key = True)
    review_body = db.Column(db.Text)
    score = db.Column(db.Float, nullable = False)
    service_id = db.Column(db.Integer, nullable = False) #service involving provider and employer
    from_user = db.Column(db.Integer, nullable = False) #user that make the review, from front-end
    user_as = db.Column(db.String(10), nullable = False) #role of user being qualified, from front-end = provider or employer

    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #owner of the review

    def __repr__(self):
        return '<Review %r>' % self.id

    def serialize(self):
        return {
            "review": self.review_body,
            "score": self.score,
            "Service": self.service_id,
            "from": self.from_user,
            "user as": self.user_as
        }