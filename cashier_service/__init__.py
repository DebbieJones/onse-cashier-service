import os
import uuid
import json
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from yaml import Loader, load

from cashier_service.rabbitevents import RabbitProducer


SWAGGER_URL = '/docs'

producer_properties = {
    'exchange': os.getenv('RABBITMQ_EXCHANGE'),
    'queue': os.getenv('RABBITMQ_QUEUE'),
    'host': os.getenv('RABBITMQ_HOST', 'localhost')
}

def create_app():
    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def get_health():
        return jsonify({"message": "OK"})

    @app.route('/cashier/create', methods=['POST'])
    def cashier_create():

        req_data = request.get_json()
        operation_id = str(uuid.uuid4())
        account_name = req_data['accountName']
        amount = req_data['amount']
        action = req_data['action']

        rabbit = RabbitProducer(producer_properties)
        rabbit.publish(json.dumps({
            'id': operation_id,
            'accountName': account_name,
            'amount': amount,
            'action': action
        }))

        return jsonify({
            'id': operation_id,
            'accountName': account_name,
            'amount': amount,
            'status': 'pending',
            'action': action
        }), 201

    app.register_blueprint(setup_swagger(), url_prefix=SWAGGER_URL)

    return app

def setup_swagger():

    swagger_yml = load(open(get_app_base_path() + '/../swagger.yml', 'r'), Loader=Loader)

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        '',
        config={
            'app_name': "Cashier Service API",
            'spec': swagger_yml
        },
    )

    return swaggerui_blueprint

def get_app_base_path():
   return os.path.dirname(os.path.realpath(__file__))