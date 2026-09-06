from flask import Blueprint, request, jsonify 
from psycopg2.extras import RealDictCursor
from flask_jwt_extended import jwt_required


try:
    from Main.db import get_db
    from Main.validation import bundle_validation 
    
except ModuleNotFoundError:
    from db import get_db
    from validation import bundle_validation 

bundles = Blueprint("bundles",__name__)


#Routes, that allow for creating a roll set, and obtaining such roll set along with its content.



"""
Confirms that the top and bottom roll ids belong to the same ds_chock number and chock type.
"""
@bundles.route("/confirm-bundle", methods=["POST"] )
@jwt_required()
def confirm_bundle():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()

        #Validation, for specific information about valdiation standards, refer to the "bundle_validation" function in "validation.py"
        top_roll, bottom_roll, installation_stand_number, top_bigger = bundle_validation(data["top_roll_id"], 
                                                                                        data["bottom_roll_id"],  data["installation_stand_number"])
        
        if top_roll == "TOP ROLL MISSING": return jsonify ({"message" : "Top Roll dosen't exist, try again"}) , 400
        if bottom_roll =="BOTTOM ROLL MISSING": return jsonify ({"message" : "Bottom Roll dosen't exist, try again"}) , 400
        if installation_stand_number is False: return jsonify ({"message" : "Installation Stand Number, Invalid. Try again."}) , 400
        if top_bigger is False: return jsonify ({"message" : "Top Roll diameter exceeds bottom roll diameter"}) , 400
            
        cur.execute("INSERT INTO bundles (top_roll_id, bottom_roll_id, ds_chock, installation_stand_number) VALUES (%s,%s,%s,%s)", 
                    (data["top_roll_id"], data["bottom_roll_id"], data["ds_chock"], data["installation_stand_number"]) )
        conn.commit()
        conn.close()
        return jsonify({"message": "Bundle Confirmed"})
    except KeyError as e:
        return jsonify ({"error" : f"Missing required field: {e}"}), 400
    except Exception as e:
        return jsonify ({"error" : f"Server error: {e}"}), 500


"""
Reads every row from the "bundles" table and returns the information back as JSON(via postman). 
"""
@bundles.route("/get-bundle", methods=["GET"] )
@jwt_required()
def get_bundle():
    try:
        conn = get_db()
        cur = conn.cursor()

        bundles = cur.execute("SELECT * FROM bundles")
        bundles = cur.fetchall()

        conn.close()
        return jsonify(bundles)
    except Exception as e:
        return jsonify({"error" : f"Server error {e}"}), 500