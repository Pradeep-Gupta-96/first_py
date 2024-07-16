from flask import request, jsonify, current_app
from bson.objectid import ObjectId

def checkapi_items():
   return "Welcome to the Home Page!"

def create_item():
    data = request.get_json()
    item = {
        'name': data.get('name')
    }
    result = current_app.db.items.insert_one(item)
    item['_id'] = str(result.inserted_id)
    return jsonify(item), 201

def get_items():
    items = list(current_app.db.items.find())
    for item in items:
        item['_id'] = str(item['_id'])
    return jsonify(items), 200

def update_item(item_id):
    data = request.get_json()
    result = current_app.db.items.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'name': data.get('name')}}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'success': True}), 200

def delete_item(item_id):
    result = current_app.db.items.delete_one({'_id': ObjectId(item_id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Item not found'}), 404
    return '', 204
