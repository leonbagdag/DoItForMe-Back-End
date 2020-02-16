"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from functools import wraps
from datetime import timedelta
import os, re
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from models import (
    db, User, Employer, Provider, Category, Contract, Request, 
    Offer, Review, Region, Comuna
)
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity, 
    verify_jwt_in_request, get_jwt_claims, get_raw_jwt, jwt_optional
)

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '1478520.Lucena1953'
jwt = JWTManager(app)
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)


def jwt_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['role'] != 'admin':
            return jsonify({'msg': 'Admins Only'}), 401
        else:
            return fn(*args, **kwargs)
    return wrapper


@jwt.user_claims_loader
def add_claims_to_access_token(user):
    if user.role == 'admin':
        return {'role': 'admin'}
    else:
        return {'role': 'client'}


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.email

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route('/')
def get_site_conf():
    """
    This is a public endpoint. Returns all categories, stats and configurations needed for the front-end app.
    this will be requested for the web app to configure at the start.
    * PUBLIC ENDPOINT *
    """
    top_categories = Category.query.all()
    top_categories.sort(reverse=True, key=lambda x: len(x.requests))
    top_categories[4:] = [] # se eliminan elementos del 4 en adelante para crear el top 4
    response_body = {
            'top_categories': list(map(lambda x: dict({**x.serialize(), 'requests': len(x.requests)}), top_categories)),
            'contracts': Contract.query.count(),
            'offers': Offer.query.count(),
            'users': User.query.count(),
            'requests': Request.query.count()
        }
    return jsonify({'stats': response_body}), 200


@app.route('/admin/region/create', methods=['POST']) #ready!
@jwt_admin_required
def create_region():

    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    name = request.json.get('name')
    if not name:
        return jsonify({'Error': 'Missing name parameter in request'}), 400

    try:
        new_region = Region(name=name)
        db.session.add(new_region)
        db.session.commit()
        return jsonify({
            'msg': 'new region crated',
            'regions': list(map(lambda x: x.serialize(), Region.query.all())),
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'Error': 'region alredy exists'}), 400


@app.route('/admin/region/<int:reg_id>', methods=['PUT', 'DELETE']) #ready!
@jwt_admin_required
def handle_regions(reg_id=None):
    """
    Edit regions stored in database. This is visible only for de Administrator
    ENDPOINT PRIVADO
    """
    region_query = Region.query.get(reg_id)

    if region_query is None:
        return jsonify({'Error': 'Region %s not found' %reg_id}), 404

    if request.method == 'DELETE': # delete 1 Region
        db.session.delete(region_query)
        db.session.commit()
        return jsonify({
            'msg': 'region deleted',
            'regions': list(map(lambda x: x.serialize(), Region.query.all()))
        }), 200
    
    if request.method == 'PUT': # update Region data
        if not request.is_json:
            return jsonify({'Error': 'Missing JSON in request'}), 400
        
        name = request.json.get('name')
        if not name:
            return jsonify({'Error': 'Missing name parameter in request'}), 400

        try:
            region_query.name = name
            db.session.commit()
            return jsonify({
                'msg': 'region updated',
                'regions': list(map(lambda x: x.serialize(), Region.query.all()))
            }), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify({'Error': 'Region name alredy exists'}), 400

    raise APIException("Invalid Method", status_code=400)


@app.route('/admin/comuna/create', methods=['POST']) #ready!
@jwt_admin_required
def create_comuna():
    
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    name = request.json.get('name')
    if not name:
        return jsonify({'Error': 'Missing name parameter in request'}), 400
    region_name = request.json.get('region')
    if not region_name:
        return jsonify({'Error': 'Missing region parameter in request'}), 400

    region_query = Region.query.filter_by(name=region_name).first()
    if region_query is None:
        return jsonify({'Error': 'Region %s not found' %region_name}), 404

    try:
        new_comuna = Comuna(name=name, region=region_query)
        db.session.add(new_comuna)
        db.session.commit()
        return jsonify({
            'msg': 'new comuna crated',
            'regions': list(map(lambda x: x.serialize(), Region.query.all()))
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'Error': 'comuna alredy exists'}), 400


@app.route('/admin/comuna/<int:comuna_id>', methods=['PUT', 'DELETE']) #ready!
@jwt_admin_required
def handle_comunas(comuna_id=None):
    """
    Edit comunas stored in database. This is visible only for de Administrator
    ENDPOINT PRIVADO
    """
    comuna_query = Comuna.query.get(reg_id)

    if comuna_query is None:
        return jsonify({'Error': 'Comuna %s not found'} %comuna_id), 404

    if request.method == 'DELETE': # delete 1 comuna
        db.session.delete(comuna_query)
        db.session.commit()
        return jsonify({
            'msg': 'comuna deleted',
            'regions': list(map(lambda x: x.serialize(), Region.query.all()))
        }), 200
    
    if request.method == 'PUT': # update comuna data
        if not request.is_json:
            return jsonify({'Error': 'Missing JSON in request'}), 400
        
        name = request.json.get('name')
        if not name:
            return jsonify({'Error': 'Missing name parameter in request'}), 400

        try:
            comuna_query.name = name
            db.session.commit()
            return jsonify({
                'msg': 'comuna updated',
                'regions': list(map(lambda x: x.serialize(), Region.query.all()))
            }), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify({'Error': 'Comuna name alredy exists'}), 400

    raise APIException("Invalid Method", status_code=400)


@app.route('/admin/category/<int:cat_id>', methods=['PUT', 'DELETE']) #ready!
@jwt_admin_required
def handle_categories(cat_id=None):
    """
    Get or Edit categories stored in database. This is visible only for de Administrator
    ENDPOINT PRIVADO
    """
    category_query = Category.query.get(cat_id)
    if category_query is None:
        return jsonify({'Error': 'Category %s not found'}), 404

    if request.method == 'DELETE': # delete 1 category
        db.session.delete(category_query)
        db.session.commit()
        return jsonify({
            'msg': 'category deleted',
            'categories': list(map(lambda x: x.serialize(), Category.query.all()))
        }), 200
    
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
            return jsonify({
                'msg': 'category updated',
                'categories': list(map(lambda x: x.serialize(), Category.query.all()))
            }), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify({'Error': 'name or logo alredy exists'}), 400

    raise APIException("Invalid Method", status_code=400)


@app.route('/admin/category/create', methods = ['POST']) #ready!
@jwt_admin_required
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
        return jsonify({
            'msg': 'category created',
            'categories': list(map(lambda x: x.serialize(), Category.query.all()))
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'Error': 'name or logo alredy exists'}), 400


@app.route('/registro', methods=['POST']) #ready
def create_new_user():
    """
    * PUBLIC ENDPOINT *
    Create an user given the email and password.
    requerido: {
        "email":"email@any.com",
        "password":"password",
        "f_name": "first_name",
        "l_name": "last_name"
    }
    respuesta: {
        "success":"nuevo usuario registrado", 200
    }
    """
        #Regular expression that checks a valid email
    ereg = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'

    if not request.is_json:
        return jsonify({'Error':'Missing JSON in request'}), 400

    email = request.json.get('email', None)
    password = request.json.get('password', None)
    fname = request.json.get('f_name', None)
    lname = request.json.get('l_name', None)

    if not (re.search(ereg, email)):
        return jsonify({'Error':'Formato del Email inválido'}), 400
    if password is None:
        return jsonify({'Error':'No se encuentra Contraseña en request'}), 400
    if fname is None:
        return jsonify({'Error': 'No se encuentra primer nombre en request'}), 400
    fname = fname.replace(" ", "").capitalize()

    if lname is None: 
        return jsonify({'Error': 'No se encuentra apellido en request'}), 400
    lname = lname.replace(" ", "").capitalize()

    try:
        new_user = User(email=email, password=password, fname=fname, lname=lname)
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"Error": "Email ya se encuentra registrado..."}), 400

    new_provider = Provider(user=new_user)
    new_employer = Employer(user=new_user)
    db.session.add(new_provider)
    db.session.add(new_employer)
    db.session.commit()

    return jsonify({"success":"Nuevo usuario registrado"}), 201  # 201 = Created

@app.route('/region/<region_name>/comunas', methods=['GET'])
def get_comunas(region_name):
    region_q = Region.query.filter(Region.name == region_name).first()

    if region_q is None:
        return jsonify({'Error': 'Region: %s no encontrada' %region_name}), 404

    return jsonify({'comunas': list(map(lambda x: x.serialize(), region_q.comunas))})

@app.route('/app-data', methods=['GET'])
def app_data():
    all_categories = Category.query.all()
    all_regions = Region.query.all()
    all_comunas = Comuna.query.all()

    response_body = {
        'all_categories': list(map(lambda x: x.serialize(), all_categories)),
        'all_regions': list(map(lambda x: x.serialize(), all_regions))
    }
    return jsonify({'app_data': response_body}), 200


@app.route('/login', methods=['POST']) #ready
def user_login():
    """
    user login with email and password
    * PUBLIC ENDPOINT *
    requerido: 
    {
        "email":"email@any.com",
        "password":"password"
    }
    return-json:  si todo está ok y usuario existe...
    {
        "access_token": "access_token_generated",
        "msg": "success",
        "user": {
            "address": {
                "comuna": <comuna_id>,
                "home_number": "home_num",
                "more_info": "more_info",
                "street": "street"
            },
            "first_name": "fname",
            "id": 9,
            "join_date": "since",
            "last_name": "lname",
            "profile_img": "link_to_img",
        }
    }
    """
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400
    
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if email is None:
        return jsonify({'Error': 'No se envió email en request'}), 400
    if password is None:
        return jsonify({'Error': 'No se envió contraseña en request'}), 400
    
    user_query = User.query.filter_by(email=email).first()
    if user_query is None:
        return jsonify({'Error': "Email no registrado."}), 404

    if user_query.password != password:
        return jsonify({'Error': 'Contraseña incorrecta, intenta de nuevo...'}), 404
    
    access_token = create_access_token(identity=user_query, expires_delta=timedelta(days=1))
    data = {
        'access_token': access_token,
        'user': user_query.serialize(),
        'logged': True,
        'success': "Conexión Exitosa, Bienvenido"
    }
    return jsonify(data), 200


@app.route('/user/profile', methods=['PUT']) #ready
@jwt_required
def set_user_profile():
    """
    actualiza los datos personales del usuario en la bd
    *PRIVATE ENDPOINT*
    requerido:
    {
        "fname":"fname",
        "lname":"lname",
        "rut": "rut",
        "rut_serial": "rut serial",
        "comuna": <comuna_id>,
        "street": "street",
        "home_number": "home_num",
        "more_info": "more_info",
        "profile_img": "url_to_img"
    }
    return json:
    {
        "id": <user_id>,
        "join_date": "date",
        "profile_img": "url_to_img",
        "first_name": "fname",
        "last_name": "lname,
        "address": {
            "street": "street",
            "home_number": "home_number",
            "more_info": "more_info",
            "comuna": <comuna_id>
        }
    }
    """
    current_user = User.query.filter(User.email == get_jwt_identity()).first()

    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    body = request.get_json()

    if body is None:
        return jsonify({'Error': 'no se encuentra datos JSON en cuerpo de request'}), 400

    if 'fname' in body:
        current_user.fname = body['fname']
    if 'lname' in body:
        current_user.lname = body['lname']
    if 'street' in body:
        current_user.street = body['street']
    if 'home_number' in body:
        current_user.home_number = body['home_number']
    if 'more_info' in body:
        current_user.more_info = body['more_info']
    if 'rut' in body:
        current_user.rut = body['rut']
    if 'rut_serial' in body:
        current_user.rut_serial = body['rut_serial']
    if 'profile_img' in body:
        current_user.profile_img = body['profile_img']
    if 'comuna' in body:
        comuna_q = Comuna.query.get(body['comuna'])
        if comuna_q is None:
            raise APIException("Comuna %s not found" %body['comuna'], status_code=404)
        current_user.comuna = comuna_q
    db.session.commit()

    return jsonify({'user': dict(
        **current_user.serialize(),
        **current_user.serialize_private_info()
    )}), 200


@app.route('/provider/categories', methods=['PUT']) #ready
@jwt_required
def update_provider_categories():
    """
    Configur las categorias favoritas del usuario como empleador
    *PRIVATE ENDPOINT*
    requerido:
    {
        "categories": [
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]
    }
    """
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    request_body = request.get_json()
    provider_id = User.query.filter(User.email == get_jwt_identity()).first().id  #ID del provedor haciendo la consulta 
    provider_q = Provider.query.get(provider_id)

    if provider_q is None:
        return jsonify({'Error': 'proveedor no existe'}), 400

    # se agregan categorias entrantes
    for c in request_body['categories']:  # recorre la lista
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

    return jsonify(dict({
        'Success': 'Categorías Actualizadas',
        **provider_q.serialize_categories() 
    })), 200


@app.route('/find/service-request', methods=['GET']) #consulted as a provider
@jwt_required
def get_service_requests():
    """
    consulta para obtener los servicios que cumplan con ciertos filtros
    *ENDPOINT PRIVADO*
    se debe enviar en url los parametros del filtro:
        ?cat1=1&cat2=2&...catn=n&comuna=<comuna_id>
    return json:
    {
    services	
        [	
           { 
                "address":	{…}
                "category"	:{…}
                "date_created":	"Mon, 13 Jan 2020 22:59:46 GMT"
                "description":	""
                "employer":	{…}
                "id":	1
                "name":	"Reparar encimera"
                "status":	"active"
            }
        ]
    }
    """
    if 'comuna' not in request.args:
        return jsonify({'Error': 'missing comuna id in request'}), 404
    
    com_filter = request.args.get('comuna')
    
    user_email = get_jwt_identity()
    current_user = User.query.filter(User.email == user_email).first()
    emp_filter = current_user.id #evita que se den como resultados servicios solicitados por el usuario haciendo la consulta actual
    cat_filter = []

    for arg in request.args:
        if 'cat' in arg:
            cat_filter.append(int(request.args[arg]))
    
    f_requests = Request.query.filter(
        Request.comuna_id == com_filter,
        Request.employer_id != emp_filter #evita que el usuaruo reciba como resultados solicitudes hechas por el mismo
    )
   
    if cat_filter != []: #Si se envian categorias como filtros en el request
        f_requests = f_requests.filter(Request.category_id.in_(cat_filter))
    else:
        user_categories = list(map(lambda x: x.id, current_user.provider.categories)) #utiliza como filtro las categorias ajustadas por el usuario
        f_requests = f_requests.filter(Request.category_id.in_(user_categories))

    f_requests.all() #se ejecutan los filtros

    not_repeated = [] # not_repeated contiene todas las solicitudes que cumplen con los filtros, pero a las que el usuario actual no ha ofertado
    for r in f_requests:
        exist = False
        for o in r.offers:
            if current_user.id == o.provider_id:
                exist = True
        if not exist:
            not_repeated.append(r)

    response_body = {
        "services": list(map(lambda x: dict({**x.serialize(), **x.serialize_employer()}), not_repeated)), 
        **current_user.serialize_provider_activity(),
        "user": current_user.serialize()
    }

    return jsonify(response_body), 200


@app.route("/service-request/<int:request_id>/offer", methods=['POST', 'GET'])
@jwt_required
def create_new_offer(request_id): #Crea una oferta a un servicio ->prov; Obtiene las offertas a un servicio ->emp
    """
    required:
    {
        "description": "description" #is optional
    }
    """
    current_user = User.query.filter(User.email == get_jwt_identity()).first()
    request_q = Request.query.get(request_id)
    if request_q is None:
        return jsonify({'Error': 'request ID not found'}), 404

    if request.method == 'POST':

        if not request.is_json:
            raise APIException('missing JSON in request', status_code=400)

        if request_q.employer_id == current_user.id:
            raise APIException('current user as employer in service-request', status_code=401)

        new_offer = Offer(
            description = request.json.get('description', None),
            provider = Provider.query.get(current_user.id), #Usuario haciendo la consulta se considera proveedor, ya que está creando una oferta de servicio
            request = request_q
        )
        db.session.add(new_offer)
        db.session.commit()
        return jsonify({'msg': 'offer created'}), 201

    if request.method == 'GET':

        if request_q.employer_id != current_user.id:
            raise APIException('access denied', status_code=401)

        return jsonify(request_q.serialize_offers()), 200


@app.route("/offer/<int:offer_id>", methods=['GET']) #As provider owner of the offer, obtiene info detallada sobre una oferta
@jwt_required
def get_offer_details(offer_id):

    current_user = User.query.filter(User.email == get_jwt_identity()).first()
    offer_q = Offer.query.get(offer_id)
    if offer_q is None:
        return jsonify({'Error': 'Offer ID not Foud'}), 404

    if offer_q.provider_id != current_user.id:
        return jsonify({"Error": "offer don't belong to current user"}), 400

    response_body = dict({
        **offer_q.serialize(),
        **offer_q.serialize_request()
    })

    return jsonify(response_body), 200


@app.route("/my-provider-info", methods=['GET'])
@jwt_required
def get_provider_info():

    current_user = User.query.filter(User.email == get_jwt_identity()).first()
    return jsonify(current_user.serialize_provider_activity()), 200


@app.route("/my-employer-info", methods=['GET'])
@jwt_required
def get_employer_info():

    current_user = User.query.filter(User.email == get_jwt_identity()).first()
    return jsonify(current_user.serialize_employer_activity()), 200


@app.route("/service-request/create", methods=["POST"]) #ready, as a employer
@jwt_required
def create_service_request():
    """
    crea una solicitud de un servicio
    requerido:
    {
        "name": "service_name",
        "description": "service_description",
        "street": "street_address",
        "home_number": "home_number_address",
        "more_info": "more info about home",
        "comuna": <comuna_id>,
        "category" <category_id
    }
    """
    current_user = User.query.filter(User.email == get_jwt_identity()).first()

    if not request.is_json:
        return jsonify({'Error': 'missing JSON in request'}), 400
    body = request.get_json()

    if 'name' not in body or body['name'] == '':
        return jsonify({'Error': 'Ingresa un nombre a tu solicitud'}), 400

    if 'description' not in body or body['description'] == '':
        return jsonify({'Error': 'ingresa una descripción a tu solicitud'}), 400

    if 'street' not in body or body['street'] == '':
        return jsonify({'Error': 'Dirección incompleta...'}), 400

    if 'home_number' not in body:
        return jsonify({'Error': 'Dirección incompleta...'}), 400
    if 'comuna' not in body or body['comuna'] == 'Comuna...':
        return jsonify({'Error': 'Selecciona tu comuna'}), 400
    if 'category' not in body:
        return jsonify({'Error': 'Selecciona una categoría para tu solicitud'}), 400

    comuna_q = Comuna.query.filter(Comuna.name == body['comuna']).first() #En body llega el nombre de la comuna
    if comuna_q is None:
        return jsonify({'Error': 'Comuna: %s no encontrada' %body['comuna']}), 404
    
    category_q = Category.query.get(int(body['category']))
    if category_q is None:
        return jsonify({'Error': 'Categoría: %s no encontrada'} %body['category']), 404

    new_request = Request(
        name = body['name'],
        description = body['description'],
        street = body['street'],
        home_number = body['home_number'],
        more_info = body['more_info'],
        employer = Employer.query.get(current_user.id), #Se considera al current_user como empleador, ya que el empleador es el unico que puede solicitar un servicio.
        category = category_q,
        comuna = comuna_q
    )
    db.session.add(new_request)
    db.session.commit()

    return jsonify({
        'Success': 'Solicitud de Servicio creada Exitosamente'
    }), 200


@app.route("/contract", methods=["GET"])
@jwt_required
def get_contract():
    """
    devuelve los contratos pertenecientes al usuario que hace la consulta.
    devuelve contratos como 
    """


@app.route("/contract/create", methods=["POST"]) #ready
@jwt_required
def create_new_contract():
    """
    crea un nuevo contrato entre un empleador y un proveedor.
    *PRIVATE ENDPOINT*
    requerido:
    {
        "provider": provider_id,
        "service": service_req_id
    }
    return-json:
    {
        "success": "contract created" ,200
    }
    """
    if not request.is_json:
        return jsonify({'Error': 'Missing JSON in request'}), 400

    current_user = User.query.filter(User.email == get_jwt_identity()).first()

    provider = request.json.get('provider', None)
    if provider is None:
        return jsonify({'Error': 'Missing provider id in body'}), 400

    service = request.json.get('service', None)
    if service is None:
        return jsonify({'Error': 'Missing service id in body'}), 400

    provider_q = Provider.query.get(provider)
    if provider_q is None:
        return jsonify({'Error', 'provider %s not found' %provider}), 404

    if provider_q.id == current_user.id:
        return jsonify({'Error': 'proveedor no puede crear un contrato'}), 401

    service_q = Request.query.get(service)
    if service_q is None:
        return jsonify({'Error', 'service %s not found' %service}), 404

    new_contract = Contract(employer=Employer.query.get(current_user.id), provider=provider_q, request=service_q) #Se considera empleador al current_user, ya que solo el empleador puede crear un contrato
    db.session.add(new_contract)
    db.session.commit() #commit3

    return jsonify({
        'msg': 'contract created',
        'contract': new_contract.serialize()
    }), 200


"""
What's missing:
    3) endpoint for update or delete a service request
    4) endpoint for get contract info as a provider
    5) endpoint for get contract info as a employer
    7) endpoint for update or delete a offer

"""


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
