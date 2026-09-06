from psycopg2.extras import RealDictCursor

try:
    from Main.db import get_db

except ModuleNotFoundError:
    from db import get_db


#Functions that validate and spellchecks information inputted, to prevent ambiguous errors, minimize typos, and ensure industry standards are met.


"Roll IDS MUST be be 6 digits Start WITH F with the NUMBER ID. If over 6, then will take the last 6 digits, if under will add 0's until digits become 6."
def roll_id_filter(roll_id):  
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


"Roll ID must, start with F, and be 6 numbers (7 characters in total)"
def validate_roll_id(roll_id):
    if not roll_id.startswith("F"): return False

    if len(roll_id) != 7: return False
    
    if not roll_id[1:].isdigit(): return False

    return True

"Roll must be top, or bottom"
def validate_position(position):
    if position not in ["TOP", "BOTTOM"]: return False

    return True

"""
Generic validation function to ensure valid numeric field. This is used often, for example in the add_roll route (rolls.py), this is used to validate diameter, 
remaining diameter, crown, etc.
"""
def validate_numeric_field(value): 
    if not isinstance(value, (int, float)): return False
    return True

"This function ensures the top roll, bottom roll, and installation stand number is VALID, also makes sure industry standards are met."
def bundle_validation(top_roll, bottom_roll, installation_stand_number):
    conn = get_db()
    cur = conn.cursor(cursor_factory= RealDictCursor)
    

    
     #Check to see if top and bottom rolls IDS actuallty EXIST in the database.
    top_roll = cur.execute("SELECT * FROM rolls WHERE roll_id = %s", (top_roll, ) ) 
    top_roll = cur.fetchone()

    bottom_roll = cur.execute("SELECT * FROM rolls WHERE roll_id = %s", (bottom_roll, ) )
    bottom_roll = cur.fetchone()

    if top_roll is None: return "TOP ROLL MISSING", None, None, None
    if bottom_roll is None: return top_roll, "BOTTOM ROLL MISSING", None, None

    #Check to see if the installation_stand_number is in the range of 1-6 and is an INTEGER.
    if not isinstance(installation_stand_number, int) or installation_stand_number not in range(1,7): installation_stand_number = False

    #Check to make sure the top roll diamater is bigger then the bottom.
    top_bigger = True
    if top_roll["diameter"] < bottom_roll["diameter"]: top_bigger = False
    
    return top_roll, bottom_roll, installation_stand_number, top_bigger
