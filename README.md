# Foodgram

## Deploy status
![Workflow Status](https://github.com/aleksej-tulko/foodgram/actions/workflows/foodgram_workflow.yml/badge.svg)


## Description

**Foodgram** is an application for creating recipes and generating a shopping cart. This project includes functionality for user registration, recipe creation, image uploads, adding recipes to favorites and the shopping cart. It also provides an API for working with the data.


## Requirements

To deploy **Foodgram** project on your local computer or server, make sure you have the following dependencies installed:

### 1. System

- **OS**: Linux, macOS or Windows with Docker or Docker Compose.
- **Docker**: required for creating containers if you want to run the application in a containerized environment. Download Docker: [https://www.docker.com/get-started](https://www.docker.com/get-started)
- **Docker Compose**: needed for easy management of multi-container applications. Download Docker Compose: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

### 2. Programs and packages

- **Python 3.8 или выше**: to work with the project, you need to have Python version 3.8 or later installed. Download Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)

- **pip**: Python package manager. Download pip: [https://pip.pypa.io/en/stable/installation/](https://pip.pypa.io/en/stable/installation/)

- **PostgreSQL**: required for working with the database if SQLite is not an option. Download PostgreSQL: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)


## Local deployment with Docker

1. Clone the repository:

    ```bash
    git clone https://github.com/aleksej-tulko/foodgram.git
    cd foodgram
    ```

2. Set up environment variables by creating a `.env` file in the root of the project and assigning the necessary values:

    ```env
    POSTGRES_USER=***
    POSTGRES_PASSWORD=***
    POSTGRES_DB=***
    DB_HOST=db
    DB_PORT=5432
    SECRET_KEY=django_secret_key
    ALLOWED_HOSTS='***,***'
    DEBUG=True
    USE_SQLITE=False
    ```

3. Launch the services:

    ```bash
    sudo docker compose up -d
    ```

6. Start migrations and copy static content:

    ```bash
    sudo docker compose -f docker-compose.production.yml pull
    sudo docker compose -f docker-compose.production.yml down
    sudo docker compose -f docker-compose.production.yml up -d
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

## Local deployment on the host

1. Clone the repository:

    ```bash
    git clone https://github.com/aleksej-tulko/foodgram.git
    cd foodgram/backend/
    ```

2. Set up environment variables by creating a `.env` file in the root of the project and assigning the necessary values:

    ```env
    POSTGRES_USER=***
    POSTGRES_PASSWORD=***
    POSTGRES_DB=***
    DB_HOST=db
    DB_PORT=5432
    SECRET_KEY=django_secret_key
    ALLOWED_HOSTS='***,***'
    DEBUG=True
    USE_SQLITE=False
    ```

3. Set up the working environment and install dependencies:

    ```bash
    python3 -m venv venv
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

4. Start migrations and create the super user:

    ```bash
    python3 manage.py migrate
    python3 manage.py createsuperuser
    ```

5. Launch the project:

    ```bash
    python3 manage.py runserver
    ```

6. (Optional) Import data set with ingredients:

    Import locally:
    ```bash
    python manage.py import_json ../data/ingredients.json
    ```

    Import on the server:
    ```bash
    cd foodgram/
    sudo docker cp data/ingredients.json foodgram-backend-1:/app
    sudo docker compose exec backend python manage.py import_json ingredients.json
    ```

## API documentation

Available on http://localhost/api/docs/ after launching Redoc:

```bash
cd foodgram/infra/
sudo docker compose up -d
```

## Author
[Aliaksei Tulko](https://github.com/aleksej-tulko)