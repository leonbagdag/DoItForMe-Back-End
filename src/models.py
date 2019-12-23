from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Join table between user and category
provider_category = db.Table('provider_catgory', db.metadata,
    db.Column("provider_id", db.Integer, db.ForeignKey("provider.id")),
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

    provider = db.relationship('Provider', back_populates='user', uselist=False, lazy=True) # 1 to 1 with provider
    employer = db.relationship('Employer', back_populates='user', uselist=False, lazy=True) # 1 to 1 with employer
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

    user = db.relationship('User', back_populates='employer', lazy=True)
    contracts = db.relationship('Contract', back_populates='employer', lazy=True)
    requests = db.relationship('Request', back_populates='employer', lazy=True)

    def __repr__(self):
        return '<Employer %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'score': self.score,
            'contracts': list(map(lambda x: x.serialize(), self.contracts)),
            'requests': list(map(lambda x: x.serialize(), self.requests)),
        }

class Provider(db.Model):
    __tablename__ = 'provider'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    score = db.Column(db.Float, default = 0)

    user = db.relationship('User', back_populates='provider', lazy=True)
    categories = db.relationship('Category', secondary=provider_category, back_populates='providers', lazy=True) #many to many with categories
    contracts = db.relationship('Contract', back_populates='provider', lazy=True)
    offers = db.relationship('Offer', back_populates='provider', lazy=True)
    requests = db.relationship('Request', back_populates='provider', lazy=True)

    def __repr__(self):
        return '<Provider %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'score': self.score,
            'categories': list(map(lambda x: x.serialize(), self.categories)),
            'contracts': list(map(lambda x: x.serialize(), self.contracts)),
            'offers': list(map(lambda x: x.serialize(), self.offers)),
            'requests': list(map(lambda x: x.serialize(), self.requests)),
        }

class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    contract_status = db.Column(db.String(10), default = 'active', nullable=False) # status options: active, paused, cancelled
    contract_start_date = db.Column(db.DateTime, default = datetime.now, nullable=False)
    contract_end_date = db.Column(db.DateTime)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))

    employer = db.relationship('Employer', back_populates='contracts', lazy=True)
    provider = db.relationship('Provider', back_populates='contracts', lazy=True)
    
    def __repr__(self):
        return '<Contract %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'status': self.contract_status,
            'start_date': self.contract_date,
            'end_date': self.contract_end_date,
            'employer_id': self.employer_id,
            'provider_id': self.provider_id,
        }

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    logo = db.Column(db.String(60), unique=True, nullable=False) #From Font-awsome

    providers = db.relationship('Provider', secondary=provider_category, back_populates='categories', lazy=True) #many to many with provider
    requests = db.relationship('Request', back_populates='category', lazy=True)

    def __repr__(self):
        return '<Category %r>' % self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo,
        }

class Profile(db.Model): # 1 to 1 rel with User
    __tablename__ = 'profile'
    id = db.Column(db.Integer, db.ForeignKey('user.id') ,primary_key=True)
    fname = db.Column(db.String(20))
    lname = db.Column(db.String(20))
    str_name = db.Column(db.String(20))
    home_number = db.Column(db.String(20))
    region = db.Column(db.String(20))
    comuna = db.Column(db.String(20))
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
            "calle": self.str_name,
            "numero": self.home_number,
        }

class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(20), nullable=False)
    str_name = db.Column(db.String(20), nullable=False)
    home_number = db.Column(db.String(20), nullable=False)
    more_info = db.Column(db.String(20))
    comuna = db.Column(db.String(20), nullable=False)
    region = db.Column(db.String(20), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.now)
    service_status = db.Column(db.String(20), default='active') #options are: active, paused, closed
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'), default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    employer = db.relationship('Employer', back_populates='requests', lazy=True)
    category = db.relationship('Category', back_populates='requests', lazy=True)
    provider = db.relationship('Provider', back_populates='requests', lazy=True)
    offers = db.relationship('Offer', back_populates='request', lazy=True)

    def __repr__(self):
        return '<Request %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'street': self.str_name,
            'number': self.home_number,
            'more_info': self.more_info,
            'comuna': self.comuna,
            'region': self.region,
            'date_created': self.creation_date,
            'status': self.service_status,
            'employer': self.employer_id,
            'category': self.category_id,
            'provider': self.provider,
            'offers': list(map(lambda x: x.serialize(), self.offers))
        }

class Offer(db.Model):
    __tablename__ = 'offer'
    id = db.Column(db.Integer, primary_key=True)
    offer_date = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.Text)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))

    provider = db.relationship('Provider', back_populates='offers', lazy=True)
    request = db.relationship('Request', back_populates='offers', lazy=True)

    def __repr__(self):
        return '<Offer %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'date': self.offer_date,
            'description': self.description,
            'provider': self.provider_id,
        }