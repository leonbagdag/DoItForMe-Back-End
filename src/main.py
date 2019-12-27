"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from models import db, User, Employer, Provider
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "hello": "world"
    }

    return jsonify(response_body), 200

@app.route('/registro', methods=['POST'])
def create_user():
    '''
    Create an user given the username, password and email. username can be = email without hostname
    '''

    body = request.get_json()

    if body is None: #400 means bad request
        raise APIException("You need to specify the request body as a json object", status_code=400)
    if 'email' not in body:
        raise APIException('You need to specify the email', status_code=400)
    if 'username' not in body:
        raise APIException('You need to specify the username', status_code=400)
    if 'password' not in body:
        raise APIException('You need to specify the password', status_code=400)

    new_user = User(email = body['email'], username = body['username'], password = body['password'])
    db.session.add(new_user)
    db.session.commit()
    new_provider = Provider(user=new_user)
    new_employer = Employer(user=new_user)
    db.session.add(new_provider)
    db.session.add(new_employer)
    db.session.commit()

    return jsonify(new_user.serialize()), 201 #201 = Created

@app.route('/user/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def get_user(user_id):
    '''
    Get Data from 1 user.
    '''
    user_query = User.query.get_or_404(user_id)

    if request.method == 'GET':
        return jsonify(dict({
            **user_query.serialize(),
            **user_query.serialize_provider_activity(),
            **user_query.serialize_employer_activity(),
        })), 200
    elif request.method == 'DELETE':
        employer_query = Employer.query.get_or_404(user_id)
        provider_query = Provider.query.get_or_404(user_id)
        db.session.delete(employer_query)
        db.session.delete(provider_query)
        db.session.delete(user_query)
        db.session.commit()
        return jsonify({"deleted": user_id}), 200
    return "Invalid method", 400

@app.route('/service_request', methods=['POST'])
def create_request():
    '''
    create service request from provider. API expects:
        - name: name of the request
        - description: text with the description of the request
        - street: name of the street where the request is made
        - home_number: number of the home in the street
        - more_info: optional adicional info about the addres
        - comuna: comuna of the service required
        - region: region of the service required
        - request_type: the type of the service request, can be open or direct
        - employer_id: id of the employer requiring the service. from Front-end
        - category_id: id of the category that require the service. from Front-end
        - provider_id: optional, required only if is a direct request. from Front-end
    '''



# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
