"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from models import db, User, Employer, Provider, Category, Contract
from sqlalchemy.exc import IntegrityError

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


@app.route('/admin/category/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_categories(id=None):
    """
    Get or Edit categories stored in database. This is visible only for de Administrator
    """
    if id is not None:
        category_query = Category.query.get(id)
        if not category_query:
            raise APIException("Category {} not found".format(id), status_code=400)

        if request.method == 'GET': # get 1 category
            return jsonify(category_query.serialize()), 200

        if request.method == 'DELETE': # delete 1 category
            db.session.delete(category_query)
            db.session.commit()
            response_body = {'message': 'deleted category: {}'.format(category_query.name)}
            return jsonify(response_body), 200
        
        if request.method == 'PUT': # update category data
            if not request.is_json:
                raise APIException("Missing JSON in request", status_code=400)

            name = request.json.get('name')
            if not name:
                raise APIException("Missing name parameter in request", status_code=400)

            logo = request.json.get('logo')
            if not logo:
                raise APIException("Missing logo parameter in request", status_code=400)

            try:
                category_query.name = name
                category_query.logo = logo
                db.session.commit()
                response_body = {'message': 'category with id: {} updated'.format(id)}
                return jsonify(response_body), 200

            except IntegrityError:
                db.session.rollback()
                raise APIException("Error, name or logo alredy exist", status_code=400)

        raise APIException("Invalid Method", status_code=400)


@app.route('/admin/category', methods = ['POST'])
def create_category():
    """
    create new category
    """
    if not request.is_json:
        raise APIException("Missing JSON in request", status_code=400)

    name = request.json.get('name')
    if not name:
        raise APIException("Missing name parameter in request", status_code=400)

    logo = request.json.get('logo')
    if not logo:
        raise APIException("Missing logo parameter in request", status_code=400)

    try:
        new_category = Category(name=name, logo=logo)
        db.session.add(new_category)
        db.session.commit()
        response_body = {'message': 'created category with id: {}'.format(new_category.id)}
        return jsonify(response_body), 201
        
    except IntegrityError:
        db.session.rollback()
        raise APIException("Error, name or logo alredy exist", status_code=400)


@app.route('/categories', methods = ['GET'])
def get_all_categories():
    """
    This is a public endpoint. Returns all categories stored in the database.
    """
    all_categories = Category.query.all()
    response_body = {'categories': list(map(lambda x: x.serialize(), all_categories))}
    return jsonify(response_body), 200


@app.route('/registro', methods=['POST'])
def create_user():
    """
    Create an user given the username, password and email. username can be = email without hostname
    """
    body = request.get_json()

    if body is None:  # 400 means bad request
        raise APIException("You need to specify the request body as a json object", status_code=400)
    if 'email' not in body:
        raise APIException('You need to specify the email', status_code=400)
    if 'username' not in body:
        raise APIException('You need to specify the username', status_code=400)
    if 'password' not in body:
        raise APIException('You need to specify the password', status_code=400)

    new_user = User(email=body['email'], username=body['username'], password=body['password'])
    db.session.add(new_user)
    db.session.commit()
    new_provider = Provider(user=new_user)
    new_employer = Employer(user=new_user)
    db.session.add(new_provider)
    db.session.add(new_employer)
    db.session.commit()

    return jsonify(new_user.serialize()), 201  # 201 = Created


@app.route('/user/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def get_user(user_id):
    """
    Get Data from 1 user.
    """
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


@app.route('/employer/<int:employer_id>', methods=['GET'])
def get_employer(employer_id):
    employer_q = Employer.query.get_or_404(employer_id)
    if request.method == 'GET':
        return jsonify({"employer": employer_q.serialize_public_info()}), 200
    return "Invalid method", 400


@app.route('/provider/<int:provider_id>/categories', methods=['PUT'])
def update_provider_categories(provider_id):
    """
    configure the categories of each user
    """
    request_body = request.get_json()
    provider_q = Provider.query.get_or_404(provider_id)
    # se agregan categorias entrantes
    for c in request_body['categories']:  # recibe una lista con el id de cada cat, dentro del valor "categories"
        new_cat = Category.query.get_or_404(c['id'])
        provider_q.categories.append(new_cat)
    db.session.commit()
    # se eliminan categorias previas que no estan en las categorias entrantes
    for d in provider_q.categories:
        exist = False
        for e in request_body['categories']:
            if d.id == e['id']:
                exist = True
        if not exist:
            provider_q.categories.remove(d)
            db.session.commit()
            exist = False

    return jsonify({'message': 'updated provider {}'.format(provider_id)}), 200


@app.route('/service_request', methods=['POST'])
def create_request():
    """
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
    """
    request_body = request.get_json()


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
