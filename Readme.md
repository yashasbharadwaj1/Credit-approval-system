# Credit Approval API

## System Components

![Credit Approval Architecture](https://github.com/yashasbharadwaj1/Credit-approval-system/assets/71028991/011cee36-e514-4107-93e9-34048bfba8f1)

credits and reference :- https://saasitive.com/tutorial/django-celery-redis-postgres-docker-compose/

### Frameworks and Tools Used:
- Django
- Django REST Framework
- Gunicorn
- PostgreSQL
- Celery (Task Queue)
- Redis (Message Broker)

## How to Run Locally
Before running the application locally, ensure you have the following dependencies installed:
- Python
- Docker
- Redis

Follow these steps to run the application locally:

Clone the repository:
   git clone <repository_url>

Navigate to the project folder:
cd <project_folder>
Build the Docker images:

docker-compose build

docker-compose up
