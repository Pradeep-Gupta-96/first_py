from flask import Blueprint
from .controllers import create_item, get_items, update_item, delete_item, checkapi_items

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def check_route():
    return checkapi_items()

@main.route('/items', methods=['POST'])
def create_route():
    return create_item()

@main.route('/items', methods=['GET'])
def read_route():
    return get_items()

@main.route('/items/<item_id>', methods=['PUT'])
def update_route(item_id):
    return update_item(item_id)

@main.route('/items/<item_id>', methods=['DELETE'])
def delete_route(item_id):
    return delete_item(item_id)
