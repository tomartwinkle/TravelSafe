from flask import Flask, request, jsonify
import googlemaps
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

gmaps = googlemaps.Client(key='AIzaSyAyyAyxzjBMd5FgUCoWRpG335omtxh7woA')

@app.route('/get_route', methods=['POST'])
def get_route():
    try:
       
        data = request.get_json()
        origin = data['origin']
        destination = data['destination']
        departure_time = data['departure_time']
        
      
        try:
            departure_datetime = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use 'YYYY-MM-DD HH:MM:SS'."}), 400
        
   
        directions = gmaps.directions(
            origin,
            destination,
            mode="driving", 
            departure_time=departure_datetime,
            alternatives=True
        )

        if not directions:
            return jsonify({"error": "No routes found."}), 404

        routes = []
        for route in directions:
            route_data = process_route(route)
            routes.append(route_data)

       
        sustainable_route = min(routes, key=lambda x: x['estimated_emissions'])

        return jsonify({"routes": routes, "sustainable_route": sustainable_route})

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def process_route(route):
    total_distance = route['legs'][0]['distance']['value'] / 1000 
    total_duration = route['legs'][0]['duration']['value'] / 60
    total_emissions = calculate_emissions(total_distance, total_duration)
    
 
    route_data = {
        "total_distance": round(total_distance, 2),
        "total_duration": round(total_duration, 2),  
        "estimated_emissions": round(total_emissions, 2), 
    }
    return route_data

def calculate_emissions(distance, duration):
    emission_factor = 0.2 
    return emission_factor * distance

if __name__ == '__main__':
    app.run(debug=True)
