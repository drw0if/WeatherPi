from flask import Flask, request, jsonify
from db import DB

app = Flask(__name__)

@app.route('/api/v1/data', methods=['POST'])
def add_record():
    # Get token
    token = request.headers.get("X-Api-Key")

    if not token:
        return jsonify({
            'error': 'Missing API token'
        }), 401

    db = DB.get_instance()

    # Check station
    station = db.get_station_by_token(token)

    if not station:
        return jsonify({
            'error': 'Invalid API token'
        }), 401
    
    data = request.get_json()

    # Validate input object
    record_schema = {
        "broadcasted_station_id": int,
        "battery": bool,
        "timestamp": int,
        "temperature": float,
        "humidity": int,
        "wind_speed": float,
        "wind_dir": int,
        "wind_gust": float,
        "rain": float,
    }

    if any([x not in data for x in record_schema.keys()]):
        return jsonify({
            'error': 'Missing field'
        }), 400

    if any([not isinstance(data[k], t) for k, t in record_schema.items()]):
        return jsonify({
            'error': 'Wrong type'
        }), 400

    # Add record
    db.add_record(data, station)

    return jsonify({}), 201


@app.route('/api/v1/data/<int:station_id>', methods=['GET'])
def get_last_record(station_id: int):
    db = DB.get_instance()

    record = db.get_last_record(station_id)

    if record:
        return jsonify(record), 200
    
    return jsonify({}), 404


if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')