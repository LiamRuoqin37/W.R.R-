# Work Roll Rechocker

> [!NOTE]
> Due to facility confidentiality and competitive industry policy, sensitive information is **REDACTED**; details are available in my resume, and further technical details can be provided for job/internship evaluation purposes.

## What is this?
This is a backend REST API for tracking work rolls sets in a industrial HSM (hot strip mill). 
This project handles roll spec data, pairing validation, and finishing stand assignments. This is all behind JWT-secured endpoints.

This was my attempt at recreating the software used as an operator in the HSM department in **[REDACTED]**. This specific program is used to track every work roll that goes through the finishing stands- diameter, crown, position pairings. Mill operators can retrieve this data in real time from the other end to validate and install the new rolls onto the finishing mill. Work Rolls must meet industrial standards.

<img width="365" height="186" alt="What Is This- Work_roll" src="https://github.com/user-attachments/assets/69d3e300-703a-4152-bcab-419917ed6c02" />

_Image Source: Analysis of roll stack deflection in a hot strip mill, Technical Papers • J. Braz. Soc. Mech. Sci. & Eng. 29 (3) • Sept 2007 • https://doi.org/10.1590/S1678-58782007000300008_

## Features
- Add, retrieve and track work rolls with all of their data (diameter, crown, finish type, and roll class).
- Bundles the appropriate work roll pairs and assigns them to a finishing stand.
- JWT authentication. Login issues a token; logout blocklists it.
- Proper validation to prevent invalid work rolls that fail to meet company standards.
- Operator authorization. Only qualified operators may use this program; every addition is traceable and documented. 
- Meaningful auto-format to increase quality of life and reduce typos. 

## Tech Stack
| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Flask |
| Database | PostgreSQL |
| Authentication | Flask-JWT-Extended, bcrypt |
| Deployment | Render |
| Test | Postman |

## Deployment
This API is deployed and live on Render.
https://roll-shop-rechocking.onrender.com

## How to run quickly (quickstart)
> [!IMPORTANT]
> Prerequisites: Python 3, PostgreSQL, Postman (or any REST client compatible with Postman collections and environments).

> [!NOTE]
> Errors is most likely due to the render database expiring due to free tier limitations. I do my best to keep it active and up to date.

1. Clone the repository.
2. Import **"Work Roll Rechocking.postman_collection"** and **"Render.postman_environment.json"** into Postman. BE sure to enable the "Render" environment 

All database tables are automatically created on first run.

### How to run locally (if quickstart does not work)

> [!IMPORTANT]
> Prerequisites: Python 3, PostgreSQL, Postman (or any REST client compatible with Postman collections and environments).

1. Clone the repository.
2. Install dependencies. In your terminal, paste: **"pip install -r requirements.txt"**
3. In your terminal, run **"psql -U postgres"**, then **"CREATE DATABASE rolls_db;"**. Type \q to exit.
4. Create a ".env" file in the root directory with the following:
   ```
	DB_HOST=localhost
	DB_NAME=rolls_db
	DB_USER= **[your postgres username]**
	DB_PASSWORD= **[your postgres password]**
	JWT_SECRET_KEY=asjidhaskdhasukdhasuod
   ```
5. Run the "app.py" (or in termianl run `python app.py`)
6. In Postman, import **"Work Roll Rechocking.postman_collection"** and **"Local.postman_environment.json"**, and enable the **"Local"** environment 

All database tables are automatically created on first run.

## API Endpoints

### Authentication (auth.py)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/add-authorized-operator` | Whitelist an operator by full name. Not case-sensitive.|
| POST | `/add-operator` | Register an account for a authorized operator. |
| POST | `/login` | Log in and receive a JWT (to access other endpoints).|
| POST | `/logout` | Blocklist the current token, revoking access.|

### Rolls (rolls.py)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/add-roll` | Add a new roll with full specification data. |
| GET | `/get-roll` | Retrieve all rolls currently in the database.|
| GET | `/get-roll/<roll_id>` | Retrieve a specific roll by ID number and review its information. |

### Bundles (bundles.py)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/confirm-bundle` | Pair a top and bottom roll and assign to a finishing stand.|
| GET | `/get-bundle` | Retrieve all bundles currently in the database.|

## Screenshots
### Successful Login
<img width="1005" height="451" alt="image" src="https://github.com/user-attachments/assets/1d7838e2-dfd4-4831-a585-87421606ff20" />


### Sample, Add Roll
<img width="714" height="467" alt="image" src="https://github.com/user-attachments/assets/8f7a0c8d-b474-4e3f-89ff-0d23cc59d49f" />

### Get roll By ID (f3000000) 
<img width="485" height="578" alt="image" src="https://github.com/user-attachments/assets/f6f0ff66-1c68-45a0-8e33-f456b12c0d63" />

### Sample Validation Error
<img width="532" height="441" alt="image" src="https://github.com/user-attachments/assets/71c4f123-5f20-43b2-94f9-fe747b766967" />



