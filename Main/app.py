from flask import Flask, request, jsonify 
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, JWTManager
from psycopg2.extras import RealDictCursor
import secrets #This is for the "JWT_secret_key"
import os

try:
    #Environment & PostgreSQL setup for creating DB connections.
    from Main.db import get_db 
    #Validation functions to deal with potential human and server errors.
    from Main.validation import roll_id_filter, validate_roll_id, validate_position, validate_numeric_field, bundle_validation
    #Authorization routes
    from Main.routes.auth import auth
    #Roll routes
    from Main.routes.rolls import rolls
    #Roll Bundle routes
    from Main.routes.bundles import bundles

except ModuleNotFoundError: #Local Module.
    from db import get_db
    from validation import roll_id_filter, validate_roll_id, validate_position, validate_numeric_field, bundle_validation
    from routes.auth import auth
    from routes.rolls import rolls
    from routes.bundles import bundles


app = Flask(__name__)

"""
JWT secret key.  (import secrets).
-Secret key to sign tokens for this app.
-Signs and verifies JWT tokens for protected routes.
"""
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

"JWT setup. handles token creation, validation and blocklist checking"
jwt = JWTManager(app)

"Blueprints. Plug auth, rolls, and bundles into the app."
app.register_blueprint(auth)
app.register_blueprint(rolls)
app.register_blueprint(bundles)


"""
Runs automatically on very single request w/@jwt_required. Checks to see "is this token on the blocklist?"

Return values:

True: request blocked
False: request goes through normally
"""
@jwt.token_in_blocklist_loader  

def check_token_loader(jwt_header, jwt_payload): 
    token = jwt_payload["jti"] #grab the unique ID of the token. 

    conn = get_db()
    cur = conn.cursor()
    blocked = cur.execute("SELECT * FROM token_blocklist WHERE token = %s", (token, ))
    blocked = cur.fetchone() 

    return blocked is not None  


"Create all database tables if they don't already exist."
def init_db():
    conn = get_db()
    cur = conn.cursor()  #A helper that sends SQL to the databse.

    """
    Table 1 (rolls): Contains top and bottom roll ids, diameter, previous diameter, remaining diameter, crown, finish, dismantle date, and roll_class.

    Columns:
    Roll ID: 6 digit numerical id with "F" infront. Text.
    Position: should be labeled 'top' or 'bottom'.
    prev_diameter: previous diameter of the roll, REAL number.
    diameter: currnet diameter of the roll, REAL number.
    remaining: remaining diameter of the roll, REAL number.
    crown: Crown of the roll, REAL number.
    finish: The finish type of the roll, TEXT.
    roll_class: TEXT.
    dismantle_date: TEXT.
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP, The exact time & date this roll was punched into the database.
    """

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
            dismantle_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
        )
    """)


    """
    Table 2 (bundles): 
    This bundles table stores a confirmed pair. One row per bundle, with top roll and bottom roll together in the same row.

    Columns:
    Top_roll id: TEXT.
    bottom_roll id: TEXT.
    ds_chock: Chock number, TEXT.
    chock_type: number ranging from 1-6, TEXT.
    installation_stand_number: INTEGER.
    """

    cur.execute("""
                 CREATE TABLE IF NOT EXISTS bundles (
                 id SERIAL PRIMARY KEY, 
                 top_roll_id TEXT, 
                 bottom_roll_id TEXT,
                 ds_chock TEXT,
                 installation_stand_number INTEGER
                 )
                 """)

    """
    Table 3 (operator_login)
    This table stores all the login info needed for each authorized operator. 

    Columns:
    full_name: Text, Not case sensative..
    username: Text, unique.
    password: Text. The "auth.py" file will hash out this password.
    crew: A,B,C or D, Text.
    shift: Integer.
    """

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

    """
    Table 4 (authorized_operators)
    Authorized users for login table. Full name basis.

    Columns:
    full_name: TEXT, not cap sensative.
    """

    cur.execute("""
                 CREATE TABLE IF NOT EXISTS authorized_operators (
                 id SERIAL PRIMARY KEY,
                 full_name TEXT
                 )
                 """)

    """
    Table 5 (token_blocklist)
    Create a blocklist for JWT. This will store invalidated tokens. For log out function.

    Columns:
    token: TEXT NOT NULL
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP, Stores the exact time.
    """
    
    cur.execute("""
                 CREATE TABLE IF NOT EXISTS token_blocklist (
                 id SERIAL PRIMARY KEY,
                 token TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                 )
                 """)

    conn.commit()
    conn.close()


init_db()


app.run(host="0.0.0.0", port=5001)



