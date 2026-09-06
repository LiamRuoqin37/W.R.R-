from flask import Blueprint, request, jsonify 
import bcrypt #for password.
#For token access once login is sucessful
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from psycopg2.extras import RealDictCursor

try:
    from Main.db import get_db
except ModuleNotFoundError:
    from db import get_db

auth = Blueprint("auth", __name__)

"""
Routes that create authorized operators and implements a login account system for said authorized operators to ensure security, and only allow access
to qualified operators.
"""



"""
Add a authorized person to use the software. Full name basis.
-Not cap sensative.
-Adds the full name into the "authorzied operators" table.
"""
@auth.route("/add-authorized-operator", methods=["POST"])
#@jwt_required()  Commented out, for debugging purposes.
def add_authorized_operator():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()

        #Avoid duplicate operators
        existing_fullname = cur.execute("SELECT * FROM authorized_operators WHERE full_name = %s", (data["full_name"].upper(), ))
        existing_fullname = cur.fetchone() #Transition to Postgres: Fetchone() is database method thus runs query, must seperate to get the actual data.

        if existing_fullname is not None: return jsonify({"Message" : "Full Name already registered."}), 400


        cur.execute("INSERT INTO authorized_operators (full_name) VALUES (%s)", (data["full_name"].upper(), )) 
        
            
        conn.commit()  
        conn.close()
        return jsonify({"Message": "Operator Authorized", "full_name": data["full_name"].upper()})

    except KeyError as e:
        return jsonify({"error" : f"Missing required field: {e}"}, 400)  
    except Exception as e:
        return jsonify({"error" : f"Server error: {e}"}), 500


"""
this creates an account for a authrozied operator. Duplicates not possible.
-Hashes the password using bcrypt.
"""
@auth.route("/add-operator", methods = ["POST"])
#@jwt_required()  Commented out, for debugging purposes.
def add_operator():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()

        #Block duplicate usernames.
        existing_username =  cur.execute("SELECT * FROM operator_login WHERE username = %s", ( data["username"], ) ) 
        existing_username = cur.fetchone()
        
        if existing_username is not None: return jsonify({"message" : "Username already taken/registered." }), 400
            
        """
        This section, will implement a hash password. This will run the password through one-way scrambler before storing it to database
        so, passwords will be stored like "$12$eImiTXuW..", unreversable from the original password. 

        When someone logs in, the program will hash what is typed it and compare the two hashes, if match: correct password.

        This is so, if someone opens my rolls_db file, they wouldnt just see all the sensative data as plain text.

        Will be relying on bcrypt library.
        
        Sources:
        https://www.geeksforgeeks.org/python/password-hashing-with-bcrypt-in-flask/
        https://stackoverflow.com/questions/77897298/storing-and-retrieving-hashed-password-in-postgres
        """
        #Hashing/encrypting the password.
        #Postgres covnersion added .decode("utg-8") due to Postgres, and bycrpt causing corrupted hashes thus invalid salt error in postman.
        hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8") 

        #Block duplicate account creation for operator
        block_duplicate = cur.execute('SELECT * FROM operator_login WHERE full_name = %s', (data["full_name"].upper(), ))
        block_duplicate = cur.fetchone()
        if block_duplicate is not None : return jsonify ({"message" : "Opeator already has an account."}), 400

        #If username is has not been made yet, then implement the login.
        cur.execute("INSERT INTO operator_login (full_name, username, password, crew, shift) VALUES (%s,%s,%s,%s,%s)", ( data["full_name"].upper(), data["username"] ,
                                                                                                            hashed_password, data["crew"], data["shift"]) )
        conn.commit()
        conn.close()
        return jsonify( {"Message": "Operator Added"})
    except KeyError as e:
        return jsonify({"error": f"Missing required field {e}"}), 400
    except Exception as e:
        return jsonify({"error" : f"Server error: {e}"}) , 500


"""
Standard login route.
-Validates username and password against the "operator_login" table.
-Verifies operator authorization against the "authorized_operators" table.
-Generates JWT access token on successful authorization.
"""
@auth.route("/login", methods = ["POST"])
def login():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor(cursor_factory= RealDictCursor)  
        
        #Look up username in database. If no row comes back, return a 400 error.
        username_check = cur.execute("SELECT * FROM operator_login WHERE username = %s", 
            (data["username"], ))
        username_check = cur.fetchone()
        if username_check is None: return jsonify ( {"Message" : "Wrong username." } ) , 400

        if not bcrypt.checkpw(data["password"].encode("utf-8"), username_check["password"].encode("utf-8")):
            return jsonify ({"message" : "Wrong password"}), 400  #Postgres Conversion: Added .encode("utf-8") to username_check["password"].

        #Check if operator's  "full_name" exists in "authorized_operators".
        authorized_operator = cur.execute("SELECT * FROM authorized_operators WHERE full_name = %s", (username_check["full_name"],)  )
        authorized_operator = cur.fetchone()
        if authorized_operator is None: return jsonify ( {"Message" : "Operator not registered."} ), 400

        conn.commit()
        conn.close()

        #Create an access token that acts as a username.
        access_token = create_access_token(identity=data["username"])  

        return jsonify ({"message" : "login sucessful" , "Username" : data["username"], "token": access_token})
    
    except KeyError as e:
        return jsonify({"error: " f"Missing required field: {e}"}), 400
    except Exception as e:
        return jsonify({"error" : f"Server error {e}"}), 500


"""
Standard logout route.  (from flask_jwt_extended import get_jwt )
-Retrive the current JWT's jti and stores it in the "token_blocklist" table to revoke access.
"""
@auth.route("/logout" , methods=["POST"])
@jwt_required()
def logout():
    try:
        token = get_jwt()["jti"]
        conn = get_db()
        cur = conn.cursor()

        cur.execute("INSERT INTO token_blocklist (token) VALUES (%s)", (token,) ) 
        conn.commit()
        conn.close()
        return jsonify({"Message" : "Logged Out sucessfully"})
    except Exception as e:
        return jsonify({"error" : f"Server error: {e}"}), 500
