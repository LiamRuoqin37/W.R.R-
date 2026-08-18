from flask import Flask, request, jsonify #request is incoming data, jsonify is outgoign data.
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import bcrypt #for password.


#Told my app how to find my Postgres database. It's like a set of directions: 
from dotenv import load_dotenv  #Library that read .env file and loads it into the enviornment so os.getnv can grab the values
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database" : os.getenv("DB_NAME"),
    "user":os.getenv("DB_USER"),
    "password":os.getenv("DB_PASSWORD")
}


def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


import secrets

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
#For token access once login is sucessful


app = Flask(__name__)

#Secret key to sign tokens for this app.
app.config["JWT_SECRET_KEY"] = secrets.token_hex(32)
jwt = JWTManager(app)


"""
This will create a connection to a database called rolls.db. 

Table 1 (rolls): Has the top and bottom roll something something come back to this later.

Columns:
Roll ID: stores text.
'Top' and 'Bottom': stores text.
prev_diameter: previous diameter of the roll, REAL number
diameter: currnet diameter of the roll, REAL number.
remaining: remaining diameter of the roll, REAL number.
crown: Crown of the roll, REAL number.
finish: The finish type of the roll, TEXT
roll_class: TEXT
dismantle_date: TEXT


-----
Table 2 (bundles): 
This bundles table stores a confirmed pair. One row per pundle, with top roll and bottom roll together in the same row

Columns:
Top_roll id: TEXT
bottom_roll id: TEXT
ds_chock: Chock number, TEXT
chock_type: number ranging from 1-6, TEXT.
"""
def init_db():
    conn = get_db()
    cur = conn.cursor()  #A helper that sends SQL to the databse.

    #Roll Table. Contains, the roll ID and all its appropriate info.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rolls (
            id SERIAL PRIMARY KEY,
            roll_id TEXT,
            position TEXT,
            prev_diameter REAL,
            diameter REAL,
            remaining REAL,
            crown REAL,
            finish TEXT,
            roll_class TEXT,
            dismantle_date TEXT
        )
    """)

    #Bundles table. Contains the bundle of top and bottom rolls.
    cur.execute("""
                 CREATE TABLE IF NOT EXISTS bundles (
                 id SERIAL PRIMARY KEY, 
                 top_roll_id TEXT, 
                 bottom_roll_id TEXT,
                 ds_chock TEXT,
                 installation_stand_number INTEGER
                 )
                 """)

    #Login info table.
    cur.execute("""
                 CREATE TABLE IF NOT EXISTS operator_login (
                 id SERIAL PRIMARY KEY,
                 full_name TEXT,
                 username TEXT,
                 password TEXT,
                 crew TEXT,
                 shift INTEGER
                 )
                 """)

    #Authorized users for login table. Full name basis.
    cur.execute("""
                 CREATE TABLE IF NOT EXISTS authorized_operators (
                 id SERIAL PRIMARY KEY,
                 full_name TEXT
                 )
                 """)
    
    #Create a blocklist for JWT. This will store invalidated tokens. For log out function.
    cur.execute("""
                 CREATE TABLE IF NOT EXISTS token_blocklist (
                 id SERIAL PRIMARY KEY,
                 token TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                 )
                 """)
    #DELETE HERE BUT DEFAULT CURRENT_TIMESTAMP automtically filles in the cyrrent date and time when a row is inserted.
    #You need this to know how old each token is, which lets you delete the expired ones with that cleanup line.

    conn.commit()
    conn.close()

@app.route("/add-authorized-operator", methods=["POST"])
#@jwt_required()  Commented out, for debugging purposes.
def add_authorized_operator():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()

        #Avoid duplicate operators
        existing_fullname = cur.execute("SELECT * FROM authorized_operators WHERE full_name = %s", (data["full_name"].upper(), ))
        existing_fullname = cur.fetchone()  #fetchone is a databse method thus needs cur. Upper is a string methdod so no need

        if existing_fullname is not None: return jsonify({"Message" : "Full Name already registered."}), 400

        cur.execute("INSERT INTO authorized_operators (full_name) VALUES (%s)", (data["full_name"].upper(), )) 
        #For above, sqlite3.ProgrammingError: Incorrect number of bindings supplied. The current statement uses 1, and there are 10 supplied. ERROR if u didnt make data["fullname "] thingy as tuple
            

        conn.commit()  #basically anythign thats klike worker stuff so liek 99% opf stuff is cur but these are conns.
        conn.close()
        return jsonify({"Message": "Operator Authorized", "full_name": data["full_name"].upper()})

    except KeyError as e:
        return jsonify({"error" : f"Missing required field: {e}"}, 400)  #existinf_full name dadada that stuff, if send request w/p full_name then error.
    except Exception as e:
        return jsonify({"error" : f"Server error: {e}"}), 500


@app.route("/add-operator", methods = ["POST"])
#@jwt_required()  Commented out, for debugging purposes.
def add_operator():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()

        #Need to make sure to block duplicate usernames.
        existing_username =  cur.execute("SELECT * FROM operator_login WHERE username = %s", ( data["username"], ) ) #fetchone returns one row from sql or none if no row exists
        existing_username = cur.fetchone()
        
        if existing_username is not None: return jsonify({"message" : "Username already taken/registered." }), 400
            

        """
        Right now your operator_login table stores passwords as plain text. So if someone opened your rolls.db file they'd see everyone's passwords directly.
        Hashing means you run the password through a one-way scrambler before storing it. So instead of storing "password123" you store something like "$2b$12$eImiTXuWVxfM37uY4JANjQ...". You can never reverse it back to the original.
        When someone logs in, you hash what they typed and compare the two hashes. If they match, correct password.
        bcrypt is just the library that does the scrambling. One line to hash, one line to check.
        """
        #Hashing/encrypting the password.
        hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8") #Postgres covnersion added .decode("utg-8") due to Postgres, and bycrpt causing corrupted hashes thus invalid salt error in postman.

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

@app.route("/login", methods = ["POST"])
def login():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor(cursor_factory= RealDictCursor)  #The equivalent of row_factory. -> for username_check["password"]
        
        #Check to see if username and login matches.
        username_check = cur.execute("SELECT * FROM operator_login WHERE username = %s", 
            (data["username"], ))
        username_check = cur.fetchone()

        if username_check is None: return jsonify ( {"Message" : "Wrong username." } ) , 400

        if not bcrypt.checkpw(data["password"].encode("utf-8"), username_check["password"].encode("utf-8")):
            return jsonify ({"message" : "Wrong password"}), 400  #Added .encode("utf-8") to username_check["password"] , for postgres conversion.

        #check if operator's  "full_name" exists in "authorized_operators"
        #Go into operator login table find the row where username column matches whatever was sent in the request.  
        #Fetchone() grab that one matching row or none if nothing matched

        #Check if operator is authorized.
        authorized_operator = cur.execute("SELECT * FROM authorized_operators WHERE full_name = %s", (username_check["full_name"],)  )
        authorized_operator = cur.fetchone()

        if authorized_operator is None: return jsonify ( {"Message" : "Operator not registered."} ), 400

        conn.commit()
        conn.close()
        
        access_token = create_access_token(identity=data["username"])  #username so that the token knows who it belongs to.
        return jsonify ({"message" : "login sucessful" , "Username" : data["username"], "token": access_token})
    except KeyError as e:
        return jsonify({"error: " f"Missing required field: {e}"}), 400
    except Exception as e:
        return jsonify({"error" : f"Server error {e}"}), 500


"""
Runs automatically on very single request w/@jwt_required. Checks to see "is this token on the blocklist?"

Return values:

True: request blocked
False: request goes through normally
"""
@jwt.token_in_blocklist_loader  #Tells FLASK-JWT, run this function everytime someone hits a protected route, before letting the, through. In other words whenever a token is used, run this function to check if the token is revoked.
#Flask-JWT is a flask extention that lets you add JSON web token 
def check_token_loader(jwt_header, jwt_payload): #Two parts of every JWT token. Header has metadata. Payload has teh actual data like the username and JTI. DATA: the content. METAdata = the extra details, ie the file name, file size, date created etc
    token = jwt_payload["jti"] #grab the unique ID of the token. Every JWT has one 

    conn = get_db()
    cur = conn.cursor()
    blocked = cur.execute("SELECT * FROM token_blocklist WHERE token = %s", (token, ))
    blocked = cur.fetchone() 

    return blocked is not None  #variable is not None just means: does this variable actuallly have a value.


#logout route.
from flask_jwt_extended import get_jwt 
@app.route("/logout" , methods=["POST"])
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


"""
Roll IDS MUST be be 6 digits Start WITH F with the NUMBER ID. If over 6, then will take the last 6 digits, if under will add 0's until digits become 6.
"""
def roll_id_filter(roll_id):  #will be data["roll_id"]  
    characters = len(roll_id[1:])
    temp_string = ""
    
    if characters < 6: #If ID is less than 6.
        for i in range(6-characters):
            temp_string += "0"
        return "F" + temp_string + roll_id[1:]
    
    elif characters > 6: #If ID is greater than 6.
        exceed_num = int(characters-6)
        return "F" + roll_id[exceed_num+1:]
    
    return roll_id

def validate_roll_id(roll_id):
    if not roll_id.startswith("F"): return False

    if len(roll_id) != 7: return False
    
    if not roll_id[1:].isdigit(): return False

    return True

def validate_position(position):
    if position not in ["TOP", "BOTTOM"]: return False

    return True


"Generic Validation Function."
def validate_numeric_field(value): 
    if not isinstance(value, (int, float)): return False
    return True


"""
FRONTEND TASKS VIA Postman: 

Add-roll, POST: Enables the user to insert the ROLL ID and POSITION (top/bottom). Added to the rolls databse.
Get-Roll, GET: reads every row from rolls table and sends it back as JSON. 

"""
@app.route("/add-roll", methods=["POST"])
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
        

        cur.execute("INSERT INTO rolls (roll_id, position, prev_diameter, diameter, remaining, crown, finish, roll_class, dismantle_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", 
                    (roll_id, position, data["prev_diameter"], data["diameter"], data["remaining"], data["crown"], data["finish"], data["roll_class"], data["dismantle_date"])
    )
        conn.commit()
        conn.close()

        return jsonify({"Message": "Roll saved", "Roll ID": roll_id, "Position": position} )
    except KeyError as e:
        return jsonify({"error" : f"Missing required field: {e}"}), 400  #f-string insert Note.
    except Exception as e:
        return jsonify({"error" : f"Server error: {str(e)}" } ) , 500
    
    


@app.route("/get-roll", methods=["GET"])
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


def bundle_validation(top_roll, bottom_roll, installation_stand_number):
    conn = get_db()
    cur = conn.cursor(cursor_factory= RealDictCursor)
    

     
     #The WHERE roll_id = ? part filters down to just the row matching that specific roll_id, and .fetchone() grabs that single matching row.

     #Check to see if Top and Bottom rolls IDS actuallty EXIST in the databse. 
    top_roll = cur.execute("SELECT * FROM rolls WHERE roll_id = %s", (top_roll, ) ) #need to make tuple this the , at the end.  This has a ROW of the table that contains roll_id!
    top_roll = cur.fetchone()

    bottom_roll = cur.execute("SELECT * FROM rolls WHERE roll_id = %s", (bottom_roll, ) )
    bottom_roll = cur.fetchone()

    if top_roll is None: return "TOP ROLL MISSING", None, None, None
    if bottom_roll is None: return top_roll, "BOTTOM ROLL MISSING", None, None

    #Check to see if the installation_stand_number Is in the range of 1-6 and is an INTEGER.
    if not isinstance(installation_stand_number, int) or installation_stand_number not in range(1,7): installation_stand_number = False

    top_bigger = True
    if top_roll["diameter"] < bottom_roll["diameter"]: top_bigger = False
    
    return top_roll, bottom_roll, installation_stand_number, top_bigger



"""
confirm_bundle, POST: Confirms that the top and bottom roll ids belong to the same ds_chock number and chock type.
confirm_bundle, GET: reads every row from bundles table and sends it back as JSON. 


NOTE TO SELF TOP MSUT BE BIGGER THAN BOTTOM, CHOCK TYPE HAS TO BE FROM 1-6
"""
@app.route("/confirm-bundle", methods=["POST"] )
@jwt_required()
def confirm_bundle():
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()

        #Validation 
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
        return jsonify ({"error" : f"Missign required field: {e}"}), 400
    except Exception as e:
        return jsonify ({"error" : f"Server error: {e}"}), 500






@app.route("/get-bundle", methods=["GET"] )
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


init_db()

#NOTE after project done. Implement login and accout process.

app.run(host="0.0.0.0", port=5001)



