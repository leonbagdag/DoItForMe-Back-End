from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Join table between user and category
user_category = db.Table('user_category', db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10), default='client', nullable=False) # Role is client or admin
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    register_date = db.Column(db.DateTime, default=datetime.now, nullable=False)

    profile = db.relationship('Profile', back_populates='user', uselist=False, lazy=True) # 1 to 1 with profile
    reviews = db.relationship('Review', back_populates='user', lazy=True) # 1 to many with reviews
    categories = db.relationship('Category', secondary=user_category, back_populates='users', lazy=True) #many to many with categories
    offers = db.relationship('Offer', back_populates='user', lazy=True) # 1 to many with offers
    services = db.relationship('Service', back_populates='user', lazy = True) # 1 to many with service
    contracts = db.relationship('Contract', back_populates='user', lazy = True) # 1 to many with contract

    def __repr__(self):
        return '<User %r>' % self.username
    
    def serialize(self):
        return {
            "user_id": self.id,
            "username": self.username,
            "email": self.email,
            "since": self.register_date.year,
            "reviews": list(map(lambda x: x.serialize(), self.reviews)),
            "categories": list(map(lambda x: x.serialize(), self.categories)),
            "offers": list(map(lambda x: x.serialize(), self.offers)),
            "services": list(map(lambda x: x.serialize_URL(), self.services)),
            "contracts": list(map(lambda x: x.serialize_URL(), self.contracts))
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    logo = db.Column(db.String(60), unique=True, nullable=False) #From Font-awsome

    users = db.relationship('User', secondary=user_category, back_populates='categories', lazy=True) #many to many with users
    services = db.relationship('Service', back_populates='category', lazy=True) #1 to many with service

    def __repr__(self):
        return '<Category %r>' % self.name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo
        }

class Profile(db.Model): # 1 to 1 rel with User
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(80))
    lname = db.Column(db.String(80))
    region = db.Column(db.String(80))
    comuna = db.Column(db.String(80))
    address_1 = db.Column(db.String(120))
    address_2 = db.Column(db.String(120))
    rut = db.Column(db.String(10))
    rut_serial = db.Column(db.String(20))
    score_as_provider = db.Column(db.Float, default=0)
    score_as_employer = db.Column(db.Float, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship('User', back_populates='profile', lazy=True) # 1 to 1 with user

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

class Review(db.Model): #1 to many rel with User
    id = db.Column(db.Integer, primary_key=True)
    review_body = db.Column(db.Text)
    score = db.Column(db.Float, nullable=False)
    contract_id = db.Column(db.Integer, nullable=False) #contract involving provider and employer
    from_user = db.Column(db.Integer, nullable=False) #user that make the review, from front-end
    user_as = db.Column(db.String(10), nullable=False) #role of user being qualified, from front-end = provider or employer
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #owner of the review

    user = db.relationship('User', back_populates='reviews', lazy=True) # one to many with user


    def serialize(self):
        return {
            "review": self.review_body,
            "score": self.score,
            "Service": self.contract_id,
            "from": self.from_user,
            "user_as": self.user_as
        }

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_body = db.Column(db.Text)
    offer_status = db.Column(db.String(10), default='active', nullable=False)
    offer_date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #provider that owns the offer
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))

    user = db.relationship('User', back_populates='offers', lazy=True) # 1 to many with user
    service = db.relationship('Service', back_populates='offers', lazy=True) #1 to many with service

    def __repr__(self):
        return '<Offer %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'offer_body': self.offer_body,
            'offer_status': self.offer_status,
            'offer_date': self.offer_date,
            'provider': self.user_id
        }

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    provider_id = db.Column(db.Integer, default=0, nullable=False) # user winner of the contract, from front-end. If 0 is an open service req
    request_date = db.Column(db.DateTime, default = datetime.now, nullable=False)
    request_status = db.Column(db.String(10), default = 'active', nullable=False) #status options: open, paused, closed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #Employer that owns de service_request
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    user = db.relationship('User', back_populates='services', lazy=True)
    category = db.relationship('Category', back_populates='services', lazy=True) # 1 to many with category
    offers = db.relationship('Offer', back_populates='service', lazy=True) # 1 to many with offer
    contract_data = db.relationship('Contract', back_populates='service', uselist=False, lazy=True) #1 to 1 with Contract

    def __repr__(self):
        return '<Service %r>' % self.service_name

    def serialize(self):
        return {
            'service_id': self.id,
            'name': self.service_name,
            'description': self.description,
            'provider': self.provider_id,
            'date': self.request_date,
            'status': self.request_status,
            'employer': self.user_id,
            'category': self.category_id
        }

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_status = db.Column(db.String(10), default = 'active', nullable=False) # status options: active, paused, cancelled
    contract_date = db.Column(db.DateTime, default = datetime.now, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Provider that won the offer and owns the contract

    service = db.relationship('Service', back_populates='contract_data', lazy=True) #1 to 1 with service
    user = db.relationship('User', back_populates = 'contracts', lazy = True)
    
    def __repr__(self):
        return '<Contract %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'status': self.contract_status,
            'date': self.contract_date,
            'service': self.service_id
        }