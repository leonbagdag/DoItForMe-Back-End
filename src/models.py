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
    profile_img = db.Column(db.String(60))
    fname = db.Column(db.String(20))
    lname = db.Column(db.String(20))
    street = db.Column(db.String(20))
    street_number = db.Column(db.String(20))
    home_number = db.Column(db.String(20))
    region = db.Column(db.String(20))
    comuna = db.Column(db.String(20))
    rut = db.Column(db.String(10))
    rut_serial = db.Column(db.String(20))

    provider = db.relationship('Provider', back_populates='user', uselist=False, lazy=True) # 1 to 1 with provider
    employer = db.relationship('Employer', back_populates='user', uselist=False, lazy=True) # 1 to 1 with employer
    reviews_made = db.relationship('Review', back_populates='user', lazy=True) # all reviews made by the user to another user, this as a provider or employer

    def __repr__(self):
        return '<User %r>' % self.username

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'join_date': self.register_date,
            'profile_img': self.profile_img,
            'first_name': self.fname,
            'last_name': self.lname,
            'address': dict({
                'street': self.street,
                'number': self.street_number,
                'home_num': self.home_number,
                'comuna': self.comuna,
                'region': self.region,
            })
        }

    def serialize_private(self):
        return {
            'email': self.email,
            'rut': self.rut,
            'serial': self.rut_serial,
        }

    def serialize_provider(self):
        return {'provider': self.provider.serialize()}

    def serialize_employer(self):
        return {'employer': self.employer.serialize()}

class Employer(db.Model):
    __tablename__ = 'employer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    score = db.Column(db.Float, default=0)

    user = db.relationship('User', back_populates='employer', uselist=False, lazy=True)
    contracts = db.relationship('Contract', back_populates='employer', lazy=True)
    requests = db.relationship('Request', back_populates='employer', lazy=True)
    reviews = db.relationship('Review', back_populates='employer', lazy=True) # reviews obtained as employer

    def __repr__(self):
        return '<Employer %r>' % self.id

    def serialize(self):
        return {
            'score': self.score,
            'contracts': list(map(lambda x: dict({**x.serialize(), **x.serialize_provider()}), self.contracts)),
            'requests': list(map(lambda x: x.serialize(), self.requests)),
            'reviews': list(map(lambda x: x.serialize(), self.reviews)),
        }

    def serialize_info(self):
        return dict({'score': self.score}, **self.user.serialize())

class Provider(db.Model):
    __tablename__ = 'provider'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    score = db.Column(db.Float, default = 0)

    user = db.relationship('User', back_populates='provider', uselist=False, lazy=True)
    categories = db.relationship('Category', secondary=provider_category, back_populates='providers', lazy=True) #many to many with categories
    contracts = db.relationship('Contract', back_populates='provider', lazy=True)
    offers = db.relationship('Offer', back_populates='provider', lazy=True)
    requests = db.relationship('Request', back_populates='provider', lazy=True)
    reviews = db.relationship('Review', back_populates='provider', lazy=True)

    def __repr__(self):
        return '<Provider %r>' % self.id

    def serialize(self):
        return {
            'score': self.score,
            'categories': list(map(lambda x: x.serialize(), self.categories)),
            'contracts': list(map(lambda x: dict({**x.serialize(), **x.serialize_employer()}), self.contracts)),
            'offers': list(map(lambda x: x.serialize(), self.offers)),
            'requests': list(map(lambda x: x.serialize(), self.requests)),
            'reviews': list(map(lambda x: x.serialize(), self.reviews)),
        }

    def serialize_info(self):
        return dict({'score': self.score}, **self.user.serialize())

class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    contract_status = db.Column(db.String(10), default = 'active', nullable=False) # status options: active, paused, cancelled
    contract_start_date = db.Column(db.DateTime, default = datetime.now, nullable=False)
    contract_end_date = db.Column(db.DateTime)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))

    employer = db.relationship('Employer', back_populates='contracts', uselist=False, lazy=True)
    provider = db.relationship('Provider', back_populates='contracts', uselist=False, lazy=True)
    
    def __repr__(self):
        return '<Contract %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'status': self.contract_status,
            'start_date': self.contract_date,
            'end_date': self.contract_end_date,
        }
    
    def serialize_provider(self):
        return {'provider:': self.provider.user.serialize()}

    def serialize_employer(self):
        return {'employer': self.employer.user.serialize()}

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
    request_type = db.Column(db.String(20)) #Types are open request or direct request
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'), default=0) # si es una solicitud directa, se debe especificar quien es el proveedor
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    employer = db.relationship('Employer', back_populates='requests', uselist=False, lazy=True)
    category = db.relationship('Category', back_populates='requests', uselist=False, lazy=True)
    provider = db.relationship('Provider', back_populates='requests', uselist=False, lazy=True)
    offers = db.relationship('Offer', back_populates='request', lazy=True)

    def __repr__(self):
        return '<Request %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'request_type': self.request_type,
            'description': self.description,
            'street': self.str_name,
            'number': self.home_number,
            'more_info': self.more_info,
            'comuna': self.comuna,
            'region': self.region,
            'date_created': self.creation_date,
            'status': self.service_status,
            'category': self.category.serialize(),
            'provider': self.provider_id,
            'employer': self.employer.serialize_info(),
        }

class Offer(db.Model):
    __tablename__ = 'offer'
    id = db.Column(db.Integer, primary_key=True)
    offer_date = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.Text)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))

    provider = db.relationship('Provider', back_populates='offers', uselist=False, lazy=True)
    request = db.relationship('Request', back_populates='offers', uselist=False, lazy=True)

    def __repr__(self):
        return '<Offer %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'date': self.offer_date,
            'description': self.description,
            'provider': self.provider.serialize_info(),
        }

    def serialize_request(self):
        return {'request_info': self.request.serialize()}

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False) # score del 1 al 5
    body = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.now)
    review_author = db.Column(db.Integer, db.ForeignKey('user.id')) # user who makes the review
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id')) #provider being evaluated
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id')) #employer being evaluated

    user = db.relationship('User', back_populates='reviews_made', uselist=False, lazy=True) #review_author
    employer = db.relationship('Employer', back_populates='reviews', uselist=False, lazy=True)
    provider = db.relationship('Provider', back_populates='reviews', uselist=False, lazy=True)

    def __repr__(self):
        return '<Review %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'score': self.score,
            'body': self.body,
            'date': self.review_date,
            'review_author': self.user.serialize(),
        }