from flask import Blueprint, request, jsonify 
from psycopg2.extras import RealDictCursor
from flask_jwt_extended import jwt_required,get_jwt_identity

try:
    from Main.db import get_db
    from Main.validation import validate_roll_id, validate_position, validate_numeric_field, roll_id_filter

except ModuleNotFoundError:
    from db import get_db
    from validation import validate_roll_id, validate_position, validate_numeric_field, roll_id_filter


rolls = Blueprint("rolls", __name__)



#Routes for adding rolls and obtaining such rolls along with its contents.



"""
The primary tagging function used by authorized hot strip mill operators.

Insert:
roll_id, position, prev_diameter, diameter, remaining, crown, finish, roll_class, dismantle_date
"""
@rolls.route("/add-roll", methods=["POST"])
@jwt_required()
def add_roll():
    try:
        data = request.get_json(silent=True)  #silent = true: Not important just less ugliar error message: 
        conn = get_db()
        cur = conn.cursor()
        
        roll_id = data["roll_id"].replace(" ", "").upper()
        position = data["position"].upper()

        #Filter
        roll_id = roll_id_filter(roll_id)  

        #Validation
        validate_roll_id(roll_id)
        validate_position(position)
        if not validate_roll_id(roll_id): return jsonify({"error": "invalid roll_id"}), 400
        if not validate_position(position): return jsonify({"error": "invalid position"}), 400
        if not validate_numeric_field(data["diameter"]): return jsonify({"error": "invalid diameter"}), 400
        if not validate_numeric_field(data["prev_diameter"]): return jsonify({"error": "invalid prev_diameter"}), 400
        if not validate_numeric_field(data["remaining"]): return jsonify({"error": "invalid remaining"}), 400
        if not validate_numeric_field(data["crown"]): return jsonify({"error": "invalid crown"}), 400

        #Track the operator that is adding the roll.
        operator = get_jwt_identity()
        

        cur.execute("INSERT INTO rolls (roll_id, position, prev_diameter, diameter, remaining, crown, finish, roll_class, dismantle_date, operator) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)", 
                    (roll_id, position, data["prev_diameter"], data["diameter"], data["remaining"], data["crown"], data["finish"], data["roll_class"], data["dismantle_date"], operator)
    )
        conn.commit() 
        conn.close()

        return jsonify({"Message": "Roll saved", "Roll ID": roll_id, "Position": position} )
    except KeyError as e:
        return jsonify({"error" : f"Missing required field: {e}"}), 400  
    except Exception as e:
        return jsonify({"error" : f"Server error: {str(e)}" } ) , 500
    
    
"""
The function returns the operator, all the rolls currently in the database.
"""
@rolls.route("/get-roll", methods=["GET"])
@jwt_required()
def get_roll():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory= RealDictCursor)

        
        rolls = cur.execute("SELECT * FROM rolls")
        rolls = cur.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rolls])
    except Exception as e:
        return jsonify ({"error" : f"Server error: {e}"}) , 500


"""
This function is used by the operator to look up a specific roll in the database. Always grabs the latest iteration in the database.
"""
@rolls.route("/get-roll/<roll_id>", methods = ["GET"])
@jwt_required()
def get_roll_by_id(roll_id): 
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)   

        roll = cur.execute("SELECT * FROM rolls WHERE roll_id = %s ORDER BY created_at DESC LIMIT 1", (roll_id, ))
        roll = cur.fetchone()

        conn.close()

        if roll is None: return jsonify({"error" : f"Roll {roll_id} not found"}), 404

        return jsonify(dict(roll))  

    except Exception as e:
        return jsonify({"error" : f"Server error: {e}"}), 500
        
