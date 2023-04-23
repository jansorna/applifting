# Applifting Django App
- Django REST framework application with Celery build on Postgres database.


## How to start application

1. Create and activate virtual environment: `virtualenv venv && source venv/bin/activate`

2. Install requirements: `pip install -r requirements.txt`

3. Create `.env_local_dev` from `.env_local_dev_example` and add all your local properties

4. Start PostgreSQL server, create the database for the project and make sure all database related properties
in the `.env_local_dev` are correct.

5. Run `python manage.py migrate` to apply migration
   
5. Install Celery and Redis(or any other broker messenger) to run background update task

6. Start Celery worker `celery -A applifting worker -l info` which consumes background tasks

7. Start Celery beat `celery -A applifting beat -l info` which pushes update task every minute into queue

8. All endpoints are documented and described in `applifting.html` file

9. Docker file and docker-compose.yml file can be used for local testing


## Authentication
- Whole app is accessible without authentication
- Only basic authentication is implemented, for testing:
1. Firstly create user: `python manage.py createsuperuser --username username --email youremail@email.com`
2. Enter password
3. Send `post` request on `/api-token-auth` with body: `{"username": "username", "password": "your password entered in point 2"}`
4. In all request add into headers `{"Authorization": "Token token_from_point_3"}`


## Development
- Run `test.sh` before pushing - runs pylint, black, coverage and pytest


## Point for improvement
- more tests
- deployment on Heroku
