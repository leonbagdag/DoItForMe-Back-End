"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os, re
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from models import db, User, Employer, Provider, Category, Contract, Request, Offer, Review, 
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
def get_site_conf():
    """
    This is a public endpoint. Returns all categories, stats and configurations needed for the front-end app.
    this will be requested for the web app to configure at the start.
    * PUBLIC ENDPOINT *
    """
    all_categories = Category.query.all()
    response_body = {'categories': list(map(lambda x: x.serialize(), all_categories))}
    return jsonify(response_body), 200


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
    ENDPOINT PRIVADO
    """
    category_query = Category.query.get(id)
    if category_query is None:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    if request.method == 'GET': # get 1 category
        return jsonify(category_query.serialize()), 200

    if request.method == 'DELETE': # delete 1 category
        db.session.delete(category_query)
        db.session.commit()
        response_body = {'message': 'deleted category: {}'.format(category_query.name)}
        return jsonify(response_body), 200
    
    if request.method == 'PUT': # update category data, need "name" and "logo" in body req.
        if not request.is_json:
            return jsonify({'Error': 'Missing JSON in request'}), 400

        name = request.json.get('name')
        if not name:
            return jsonify({'Error': 'Missing name parameter in request'}), 400

        logo = request.json.get('logo')
        if not logo:
            return jsonify({'Error': 'Missing logo parameter in request'}), 400

        try:
            category_query.name = name
            category_query.logo = logo
            db.session.commit()
            response_body = {'message': 'category with id: {} updated'.format(id)}
            return jsonify(response_body), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify({'Error': 'name or logo alredy exists'}), 400

    raise APIException("Invalid Method", status_code=400)


@app.route('/admin/category', methods = ['POST'])
def create_category():
    """
    create new category as Administrator.
    need "name" and "logo" in body request
    ENDPOINT PRIVADO
    """
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    name = request.json.get('name')
    if not name:
        return jsonify({'Error': 'Missing name parameter in request'}), 400

    logo = request.json.get('logo')
    if not logo:
        return jsonify({'Error': 'Missing logo parameter in request'}), 400

    try:
        new_category = Category(name=name, logo=logo)
        db.session.add(new_category)
        db.session.commit()
        response_body = {'message': 'created category with id: {}'.format(new_category.id)}
        return jsonify(response_body), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'Error': 'name or logo alredy exists'}), 400


@app.route('/registro', methods=['POST'])
def create_user():
    """
    Create an user given the email and password.
    * PUBLIC ENDPOINT *
    """
        #Regular expression that checks a valid email
    ereg = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        #Regular expression that checks a valid password
    preg = '^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$'

    if not request.is_json:
        return jsonify({'Error':'Missing JSON in request'}), 400

    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not (re.search(ereg, email)):
        return jsonify({'Error':'Invalid email format'}), 400
    if password is None:
        return jsonify({'Error':'password parameter not found in requesr'}), 400

    try:
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"Error": "email already exists"}), 400

    new_provider = Provider(user=new_user)
    new_employer = Employer(user=new_user)
    db.session.add(new_provider)
    db.session.add(new_employer)
    db.session.commit()

    return jsonify({"success":"nuevo usuario registrado"}), 201  # 201 = Created


@app.route('/login', methods=['POST'])
def user_login():
    """
    user login with email and password
    * PUBLIC ENDPOINT *
    """
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400
    
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if email is None:
        return jsonify({'Error': 'Missin email parameter in JSON'}), 400
    if password is None:
        return jsonify({'Error': 'Missing password parameter in JSON'}), 400
    
    user_query = User.query.filter_by(email=email).first()
    if user_query is None:
        return jsonify({'Error': "email: '%s' not found" %email}), 404
    
    if user_query.password == password:
        data = {
            'access_token': "",
            'user': dict({
                **user_query.serialize(),
                **user_query.serialize_provider_activity(),
                **user_query.serialize_employer_activity()
            }),
            'msg': 'success'
        }
        return jsonify(data), 200

    return jsonify({'Error': 'wrong password, try again...'}), 404


@app.route('/user/<int:user_id>/profile', methods=['PUT'])
def set_user_profile(user_id):
    """
    actualiza los datos personales del usuario en la bd
    *PRIVATE ENDPOINT*
    """
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    user_query = User.query.get(user_id)
    if user_query is None:
        return jsonify({'Error': 'usuario %s no encontrado' %user_id}), 400
    
    body = request.get_json()

    if body is None:
        return jsonify({'Error': 'no se encuentra datos JSON en cuerpo de request'}), 400

    if 'fname' in body:
        user_query.fname = body['fname']
    if 'lname' in body:
        user_query.lname = body['lname']
    if 'street' in body:
        user_query.street = body['street']
    if 'home_number' in body:
        user_query.home_number = body['home_number']
    if 'more_info' in body:
        user_query.more_info = body['more_info']
    if 'region' in body:
        user_query.region = body['region']
    if 'comuna' in body:
        user_query.comuna = body['comuna']
    if 'rut' in body:
        user_query.rut = body['rut']
    if 'rut_serial' in body:
        user_query.rut_serial = body['rut_serial']

    db.session.commit()

    return jsonify({'success': 'perfil de usuario %s actualizado' %user_id}), 200


@app.route('/employer/<int:employer_id>', methods=['GET'])
def get_employer(employer_id):
    """
    consulta publica sobre un empleador
    *ENDPOINT PUBLICO*
    """
    employer_q = Employer.query.get(employer_id)
    if employer_q is None:
        return jsonify({'Error': 'empleador %s no encontrado' %employer_id}), 400

    return jsonify({"employer": employer_q.serialize_public_info()}), 200


@app.route('/provider/<int:provider_id>', methods=['GET'])
def get_provider(provider_id):
    """
    consulta publica sobre un proveedor
    *ENDPOINT PUBLICO*
    """
    provider_q = Provider.query.get(provider_id)
    if provider_q is None:
        return jsonify({'Error': 'provedor {} no existe'.format(provider_id)}), 400

    return jsonify({"provider": provider_q.serialize_public_info()}), 200


@app.route('/provider/<int:provider_id>/categories', methods=['PUT'])
def update_provider_categories(provider_id):
    """
    Configur las categorias favoritas del usuario como empleador
    *PRIVATE ENDPOINT*
    """
    request_body = request.get_json()
    provider_q = Provider.query.get(provider_id)
    if provider_q is None:
        return jsonify({'Error': 'proveedor %s no existe' %provider_id}), 400

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

    return jsonify({'message': 'provider {} updated'.format(provider_id)}), 200


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
