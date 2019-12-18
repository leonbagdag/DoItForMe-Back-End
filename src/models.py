from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    role = db.Column(db.String(10), default = 'user', nullable = False) # Role is user or admin
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    user_profile = db.relationship()

    def __repr__(self):
        return '<User %r>' %self.username
    
    def serialize(self):
        return {
            "username": self.username,
            "email": self.email
        }

class Userprofile(db.Model): # Relación 1 a 1 con User
    __tablename__ = 'userinfo'
    id = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String(80), nullable = False)
    lname = db.Column(db.String(80), nullable = False)
    region = db.Column(db.String(80), nullable = True)
    comuna = db.Column(db.String(80), nullable = True)
    address_1 = db.Column(db.String(120), nullable = True)
    address_2 = db.Column(db.String(120), nullable = True)
    rut = db.Column(db.String(10), nullable = True)
    rut_serial = db.Column(db.String(20), nullable = True)
    score_as_provider = db.Column(db.Float, default = 0)
    score_as_employer = db.Column(db.Float, default = 0)
    info_owner = db.Column(db.Integer, db.ForeignKey('User.id'))

    def __repr__(self):
        return '<User %r>' %self.fname
    
    def serialize(self):
        return {
            "firstName": self.fname,
            "lastName": self.lname,
            "score_as_provider": self.score_as_provider,
            "score_as_employer": self.score_as_employer
        }

class Review(db.Model): #Relación 1 a muchos con User
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key = True)
    userRole = db.Column(db.String(10), nullable = False) #Provider or Employer
    review = db.Column(db.Text, nullable = True)
    score = db.Column(db.Float, nullable = False)
    serviceID = db.Column(db.Integer, nullable = False)
    fromUserID = db.Column(db.Integer, nullable = False) #Must be opposite to userRole

    def __repr__(self):
        return '<Review %r>' %self.id

    def serialize(self):
        return {
            "review": self.review,
            "score": self.score,
            "from": self.fromUserID,
            "Service": self.serviceID,
        }