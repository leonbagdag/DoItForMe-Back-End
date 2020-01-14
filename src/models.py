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
    password = db.Column(db.String(30), nullable=False)
    register_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    profile_img = db.Column(db.String(60))
    fname = db.Column(db.String(30))
    lname = db.Column(db.String(30))
    street = db.Column(db.String(120))
    home_number = db.Column(db.String(20))
    more_info = db.Column(db.String(60))
    rut = db.Column(db.String(20))
    rut_serial = db.Column(db.String(30))
    comuna_id = db.Column(db.Integer, db.ForeignKey('comuna.id'))

    provider = db.relationship('Provider', back_populates='user', uselist=False, lazy=True) # 1 to 1 with provider
    employer = db.relationship('Employer', back_populates='user', uselist=False, lazy=True) # 1 to 1 with employer
    reviews_made = db.relationship('Review', back_populates='user', lazy=True) # all reviews made by the user to another user, this as a provider or employer
    comuna = db.relationship('Comuna', back_populates='users', uselist=False, lazy = True)

    def __repr__(self):
        return '<User %r>' % self.username

    def serialize(self):
        return {
            'id': self.id,
            'join_date': self.register_date,
            'profile_img': self.profile_img,
            'first_name': self.fname,
            'last_name': self.lname,
            'address': dict({
                'street': self.street,
                'home_number': self.home_number,
                'more_info': self.more_info,
                'comuna': self.comuna_id
            })
        }

    def serialize_private_info(self):
        return {
            'email': self.email,
            'rut': self.rut,
            'serial': self.rut_serial,
        }

    def serialize_provider_activity(self):
        return {'provider': self.provider.serialize()}

    def serialize_employer_activity(self):
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
            'contracts': list(map(lambda x: x.serialize(), self.contracts)),
            'requests': list(map(lambda x: x.serialize(), self.requests)),
            'reviews': list(map(lambda x: x.serialize(), self.reviews)),
        }

    def serialize_public_info(self):
        return dict({'score': self.score}, **self.user.serialize())


class Provider(db.Model):
    __tablename__ = 'provider'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    score = db.Column(db.Float, default = 0)

    user = db.relationship('User', back_populates='provider', uselist=False, lazy=True)
    categories = db.relationship('Category', secondary=provider_category, back_populates='providers', lazy=True) #many to many with categories
    contracts = db.relationship('Contract', back_populates='provider', lazy=True)
    offers = db.relationship('Offer', back_populates='provider', lazy=True)
    reviews = db.relationship('Review', back_populates='provider', lazy=True)

    def __repr__(self):
        return '<Provider %r>' % self.id

    def serialize_categories(self):
        return {
            'categories': list(map(lambda x: x.serialize(), self.categories))
        }

    def serialize(self):
        return {
            'score': self.score,
            'contracts': list(map(lambda x: x.serialize(), self.contracts)),
            'offers': list(map(lambda x: x.serialize(), self.offers)),
            'reviews': list(map(lambda x: x.serialize(), self.reviews)),
            'categories': list(map(lambda x: x.serialize(), self.categories))
        }

    def serialize_public_info(self):
        return dict({
            'score': self.score, 
            'categories': list(map(lambda x: x.serialize(), self.categories))},
            **self.user.serialize()
        )


class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    contract_status = db.Column(db.String(10), default = 'active', nullable=False) # status options: active, paused, cancelled
    contract_start_date = db.Column(db.DateTime, default = datetime.now, nullable=False)
    contract_end_date = db.Column(db.DateTime)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('request.id'))

    employer = db.relationship('Employer', back_populates='contracts', uselist=False, lazy=True)
    provider = db.relationship('Provider', back_populates='contracts', uselist=False, lazy=True)
    request = db.relationship('Request', back_populates='contract', uselist=False, lazy=True)
    
    def __repr__(self):
        return '<Contract %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'status': self.contract_status,
            'start_date': self.contract_date,
            'end_date': self.contract_end_date,
            'service_id': self.service_id
        }
    
    def serialize_provider(self):
        return {'provider:': self.provider.serialize_public_info()}

    def serialize_employer(self):
        return {'employer': self.employer.serialize_public_info()}

    def serialize_service_request(self):
        return {'service': self.request.serialize()}


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
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
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    street = db.Column(db.String(60), nullable=False)
    home_number = db.Column(db.String(20), nullable=False)
    more_info = db.Column(db.String(60))
    creation_date = db.Column(db.DateTime, default=datetime.now)
    service_status = db.Column(db.String(20), default='active') #options are: active, paused, closed
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    comuna_id = db.Column(db.Integer, db.ForeignKey('comuna.id'))

    employer = db.relationship('Employer', back_populates='requests', uselist=False, lazy=True)
    category = db.relationship('Category', back_populates='requests', uselist=False, lazy=True)
    offers = db.relationship('Offer', back_populates='request', lazy=True)
    contract = db.relationship('Contract', back_populates='request', uselist=False, lazy=True)
    comuna = db.relationship('Comuna', back_populates='requests', uselist=False, lazy=True)

    def __repr__(self):
        return '<Request %r>' % self.i

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'date_created': self.creation_date,
            'status': self.service_status,
            'category': self.category.serialize(),
            'address': {
                'street': self.street,
                'home_number': self.home_number,
                'more_info': self.more_info,
                'comuna': self.comuna.serialize(),
            }
        }

    def serialize_offers(self):
        return {'offers': list(map(lambda x: x.serialize(), self.offers))}

    def serialize_employer(self):
        return {'employer': self.employer.serialize_public_info()} #employer who made the request

    def serialize_contract (self):
        if self.contract is None:
            return {'contract': "No contract"}
        return {'contract': self.contract.serialize()}

class Offer(db.Model):
    __tablename__ = 'offer'
    id = db.Column(db.Integer, primary_key=True)
    offer_date = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default='active')
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
        }

    def serialize_request(self):
        return {'request_info': self.request.serialize()}

    def serlialize_provider(self):
        return {'provider': self.provider.serialize_public_info()}


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False) # score del 1 al 5
    body = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.now)
    review_author = db.Column(db.Integer, db.ForeignKey('user.id')) # user who makes the review
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id')) #provider being evaluated
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id')) #employer being evaluated

    user = db.relationship('User', back_populates='reviews_made', uselist=False, lazy=True)  #review_author
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
    
    def serialize_employer(self): #employer who owns the review
        return {'employer': self.employer.serialize_public_info()}

    def serialize_provider(self): #provider who owns the review
        return {'provider': self.provider.serialize_public_info()}


class Region(db.Model):
    __tablename__ = 'region'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable = False, unique=True)

    comunas = db.relationship('Comuna', back_populates='region', lazy=True)

    def __repr__(self):
        return '<Region %r>' %self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'comunas': list(map(lambda x: x.serialize(), self.comunas))
        }


class Comuna(db.Model):
    __tablename__ = 'comuna'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable = False, unique=True)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'))

    region = db.relationship('Region', back_populates='comunas', uselist=False, lazy=True)
    users = db.relationship('User', back_populates='comuna', lazy=True)
    requests = db.relationship('Request', back_populates='comuna', lazy=True)

    def __repr__(self):
        return '<Comuna %r>' %self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }
    
    def serialize_region(self):
        return {
            "region": self.region.serialize()
        }

    def serialize_users(self):
        return {
            "users": list(map(lambda x: x.serialize(), self.users))
        }

    def serialize_services(self):
        return {
            "services": list(map(lambda x: x.serialize(), self.requests))
        }