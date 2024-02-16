from django.db import models

class Customer(models.Model):
    customer_id = models.IntegerField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField(default=15)
    phone_number = models.BigIntegerField()
    monthly_salary = models.BigIntegerField()
    approved_limit = models.BigIntegerField()

class Loan(models.Model):
    customer_id = models.IntegerField() 
    loan_id = models.IntegerField()
    loan_amount = models.IntegerField()
    tenure = models.IntegerField()
    interest_rate = models.FloatField()
    monthly_payment = models.FloatField()
    emis_paid_on_time = models.IntegerField()
    date_of_approval = models.DateField()
    end_date = models.DateField()