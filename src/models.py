from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Join table between user and category
provider_category = db.Table('provider_catgory', db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"))
)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10), default='client', nullable=False) # Role is client or admin
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    register_date = db.Column(db.DateTime, default=datetime.now, nullable=False)

    provider = db.relationship('Provider', back_populates='user', uselist=False, lazy=True)
    employer = db.relationship('Employer', back_populates='user', uselist=False, lazy=True)
    profile = db.relationship('Profile', back_populates='user', uselist=False, lazy=True) # 1 to 1 with profile

    def __repr__(self):
        return '<User %r>' % self.username
    
    def serialize(self):
        return {
            "user_id": self.id,
            "username": self.username,
            "email": self.email,
            "since": self.register_date.year,
            "profile": self.profile.serialize(),
            "provider": self.provider.serialize(),
            "employer": self.employer.serialize(),
        }

class Employer(db.Model):
    __tablename__ = 'employer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    score = db.Column(db.Float, default=0)

    def __repr__(self):
        return '<Employer %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'score': self.score,
        }

class Provider(db.Model):
    __tablename__ = 'provider'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    score = db.Column(db.Float, default = 0)

    categories = db.relationship('Category', secondary=provider_category, back_populates='providers', lazy=True) #many to many with categories

    def __repr__(self):
        return '<Provider %r', % self.id

    def serialize(self):
        return {
            'id': self.id,
            'score': self.score,
            'categories': list(map(lambda x: x.serialize(), self.categories)),
        }

class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    contract_status = db.Column(db.String(10), default = 'active', nullable=False) # status options: active, paused, cancelled
    contract_start_date = db.Column(db.DateTime, default = datetime.now, nullable=False)
    contract_end_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return '<Contract %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'status': self.contract_status,
            'start_date': self.contract_date,
            'end_date': self.contract_end_date
        }

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    logo = db.Column(db.String(60), unique=True, nullable=False) #From Font-awsome

    providers = db.relationship('Provider', secondary=provider_category, back_populates='categories', lazy=True) #many to many with provider

    def __repr__(self):
        return '<Category %r>' % self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo
        }

class Profile(db.Model): # 1 to 1 rel with User
    __tablename__ = 'profile'
    id = db.Column(db.Integer, db.ForeignKey('user.id') ,primary_key=True)
    fname = db.Column(db.String(80))
    lname = db.Column(db.String(80))
    region = db.Column(db.String(80))
    comuna = db.Column(db.String(80))
    address_1 = db.Column(db.String(120))
    address_2 = db.Column(db.String(120))
    rut = db.Column(db.String(10))
    rut_serial = db.Column(db.String(20))

    user = db.relationship('User', back_populates='profile', lazy=True) # 1 to 1 with user

    def __repr__(self):
        return '<Profile %r>' % self.fname
    
    def serialize(self):
        return {
            "profile_id": self.id,
            "firstName": self.fname,
            "lastName": self.lname,
            "region": self.region,
            "comuna": self.comuna,
            "address1": self.address_1,
            "address2": self.address_2,
        }

class Review(db.Model): #1 to many rel with User
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    review_body = db.Column(db.Text)
    score = db.Column(db.Float, nullable=False)
    contract_id = db.Column(db.Integer, nullable=False) #contract involving provider and employer, from front-end
    from_user = db.Column(db.Integer, nullable=False) #user that make the review, from front-end

    def serialize(self):
        return {
            "review_id": self.id,
            "review": self.review_body,
            "review_as": self.user_as
            "score": self.score,
            "contract": self.contract_id,
        }