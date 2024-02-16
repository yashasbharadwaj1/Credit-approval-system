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

## api calls - please use http://localhost/ , 

http://localhost/api/populate/loan/data

http://localhost/api/populate/customer/data

http://localhost/api/view-loan/5930/

http://localhost/api/view-loans/270/

http://localhost/api/register 
{
    "first_name": "iron",
    "last_name": "man",
    "age": 22,
    "monthly_income": 30000,
    "phone_number": 8892113486
}


http://localhost/api/create-loan/
{
    "customer_id": 270,
    "loan_amount": 100000,
    "interest_rate": 8.2,
    "tenure": 12
}


## Working screen shots 

conatiners running
<img width="754" alt="containers running" src="https://github.com/yashasbharadwaj1/Credit-approval-system/assets/71028991/c36a7f17-035d-48c6-8fd4-bf5a92503b30">

postgres db 
<img width="920" alt="postgres db" src="https://github.com/yashasbharadwaj1/Credit-approval-system/assets/71028991/75558cc8-e217-4c83-9fae-11e63604cdbd">


