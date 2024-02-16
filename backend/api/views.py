from api.tasks import populate_customer_data_from_excel, populate_loan_data_from_excel
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from api.models import Customer, Loan
from django.db.models import Max
from dateutil.relativedelta import relativedelta
from random import randint
from django.utils import timezone


@api_view(["GET"])
def load_customer_data(request):
    populate_customer_data_from_excel.delay()
    return Response({"status": "populating customer data started ..."})


@api_view(["GET"])
def load_loan_data(request):
    populate_loan_data_from_excel.delay()
    return Response({"status": "populating loan data started ..."})


@api_view(["POST"])
def register_customer(request):
    data = request.data

    errors = {}
    # Customer details validation
    first_name = data.get("first_name")
    if first_name is None:
        errors["first_name"] = "First name is required."
    elif not isinstance(first_name, str) or len(first_name) > 100 or first_name == "":
        errors["first_name"] = "Invalid or too long first name"

    last_name = data.get("last_name")
    if last_name is None:
        errors["last_name"] = "Last name is required."
    elif not isinstance(last_name, str) or len(last_name) > 100 or last_name == "":
        errors["last_name"] = "Invalid or too long last name"

    age = data.get("age")
    if age is None:
        errors["age"] = "Age is required."
    elif not isinstance(age, int) or age < 0:
        errors["age"] = "Invalid age"

    phone_number = data.get("phone_number")
    if phone_number is None:
        errors["phone_number"] = "Phone number is required."
    elif not isinstance(phone_number, int) or len(str(phone_number)) != 10:
        errors["phone_number"] = "Invalid phone number"

    monthly_income = data.get("monthly_income")
    if monthly_income is None:
        errors["monthly_income"] = "Monthly income is required."
    elif not isinstance(monthly_income, int) or monthly_income < 0:
        errors["monthly_income"] = "Invalid monthly income"
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    approved_limit = round(36 * monthly_income, -5)

    last_customer_id = (
        Customer.objects.aggregate(Max("customer_id"))["customer_id__max"] or 0
    )

    new_customer_id = last_customer_id + 1

    while Customer.objects.filter(customer_id=new_customer_id).exists():
        new_customer_id += 1

    # check if customer already exists
    existing_customer = Customer.objects.filter(
        first_name=first_name,
        last_name=last_name,
        age=age,
        monthly_salary=monthly_income,
        phone_number=phone_number,
    ).first()

    if existing_customer:
        response_data = {
            "message": "Customer already registered",
            "customer_id": existing_customer.customer_id,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    customer = Customer.objects.create(
        customer_id=new_customer_id,
        first_name=first_name,
        last_name=last_name,
        age=age,
        monthly_salary=monthly_income,
        approved_limit=approved_limit,
        phone_number=phone_number,
    )

    response_data = {
        "customer_id": customer.customer_id,
        "name": f"{customer.first_name} {customer.last_name}",
        "age": customer.age,
        "monthly_income": customer.monthly_salary,
        "approved_limit": customer.approved_limit,
        "phone_number": customer.phone_number,
    }

    return Response(response_data)


@api_view(["POST"])
def check_eligibility(request):
    data = request.data

    # Perform data type validation
    errors = {}

    customer_id = data.get("customer_id")
    if customer_id is None:
        errors["customer_id"] = "Customer ID is required."
    elif not isinstance(customer_id, int):
        errors["customer_id"] = "Customer ID must be an integer."
    elif customer_id <= 0:
        errors["customer_id"] = "Loan amount must be greater than zero."

    # Loan amount
    loan_amount = data.get("loan_amount")
    if loan_amount is None:
        errors["loan_amount"] = "Loan amount is required."
    elif not isinstance(loan_amount, (int, float)):
        errors["loan_amount"] = "Loan amount must be a numeric value."
    elif loan_amount <= 0:
        errors["loan_amount"] = "Loan amount must be greater than zero."

    # Interest rate
    interest_rate = data.get("interest_rate")
    if interest_rate is None:
        errors["interest_rate"] = "Interest rate is required."
    elif not isinstance(interest_rate, (int, float)):
        errors["interest_rate"] = "Interest rate must be a numeric value."
    elif interest_rate <= 0:
        errors["interest_rate"] = "Interest rate must be greater than zero."

    # Tenure
    tenure = data.get("tenure")
    if tenure is None:
        errors["tenure"] = "Tenure is required."
    elif not isinstance(tenure, int):
        errors["tenure"] = "Tenure must be an integer."
    elif tenure <= 0:
        errors["tenure"] = "Tenure must be greater than zero."

    # Check if any errors occurred
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    response_data = decide_loan_eligibility(
        customer_id, loan_amount, interest_rate, tenure
    )
    return Response(response_data)


def decide_loan_eligibility(customer_id, loan_amount, interest_rate, tenure):
    loans = Loan.objects.filter(customer_id=customer_id)
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {"message": f"customer {customer_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    approved_limit = customer.approved_limit

    total_num_of_loans = loans.count()
    print(total_num_of_loans, "total_num_of_loans")

    if total_num_of_loans != 0:

        # credit score components
        # reference :- https://www.wellsfargo.com/financial-education/credit-management/calculate-credit-score/

        # component 1  one :- payment history
        past_loans_paid_on_time = sum(loan.emis_paid_on_time for loan in loans)
        print(past_loans_paid_on_time, "past_loans_paid_on_time")
        payment_history_score = past_loans_paid_on_time / total_num_of_loans
        print(payment_history_score, "payment_history_score")

        # Component 2 How much you owe

        # list of load ids that are paid by customer
        loans_paid = []
        # map of loan id to amount owed on that loan
        loans_pending = {}

        for loan in loans:
            loan_id_in_db = loan.loan_id
            tenure_in_db = loan.tenure
            emis_paid_in_db = loan.emis_paid_on_time
            loan_amount_in_db = loan.loan_amount
            interest_rate_in_db = loan.interest_rate

            pending_months = tenure_in_db - emis_paid_in_db

            if pending_months > 0:
                monthly_installment = calculate_monthly_installment(
                    loan_amount_in_db, tenure_in_db, interest_rate_in_db
                )
                amount_owed = round(monthly_installment) * pending_months
                amount_owed = round(amount_owed, 2)
                loans_pending[loan_id_in_db] = amount_owed
            else:
                loans_paid.append(loan_id_in_db)

        print(loans_paid, "loans_paid")
        print(loans_pending, "loans_pending")

        total_amount_owed = sum(amount_owed for amount_owed in loans_pending.values())
        print(total_amount_owed, "Total amount owed")

        max_amount_owed = (
            approved_limit  # Since approved limit is the maximum amount owed
        )
        print(max_amount_owed, "Max amount")
        amount_owed_score = total_amount_owed / max_amount_owed

        print(
            amount_owed_score,
            "Score for how much the customer has to pay ",
        )

        # Component 3 :- length of credit history
        total_num_of_loans_taken = loans.count()

        # Component 4  :- Recent credit activity
        current_year_loans = loans.filter(date_of_approval__year=2024).count()

        loan_approved_volume_so_far = sum(loan.loan_amount for loan in loans)
        print(loan_approved_volume_so_far, "loan_approved_volume")

        credit_score = (
            payment_history_score
            + amount_owed_score
            + total_num_of_loans_taken
            + current_year_loans
        )
        credit_score = round(credit_score)
        print(credit_score, "credit_score")

        # Check loan eligibility based on credit score
        loan_amount_asked_by_customer = loan_amount
        available_amount_threshold = approved_limit - loan_approved_volume_so_far
        if loan_amount_asked_by_customer > available_amount_threshold:
            return {
                "customer_id": customer_id,
                "approval": False,
                "interest_rate": interest_rate,
                "tenure": tenure,
                "message": "loan amount asked by the customer is grater than the approved limit threshold",
            }

        elif credit_score > 50:
            corrected_interest_rate = interest_rate
        elif 50 >= credit_score > 30:
            corrected_interest_rate = max(interest_rate, 12)
        elif 30 >= credit_score > 10:
            corrected_interest_rate = max(interest_rate, 16)
        else:
            return {
                "customer_id": customer_id,
                "approval": False,
                "interest_rate": interest_rate,
                "tenure": tenure,
                "message": "customers credit score is less than 10",
            }

    else:
        #  if customer has not taken any loan then we cant compute credit score
        corrected_interest_rate = interest_rate

    # # Compute EMI
    customer_monthly_salary = customer.monthly_salary
    print(customer_monthly_salary, "customer_monthly_salary")
    monthly_installment = calculate_monthly_installment(
        loan_amount, tenure, corrected_interest_rate
    )
    monthly_installment = round(monthly_installment, 2)
    print(monthly_installment, "monthly installment")

    if monthly_installment > customer_monthly_salary:
        return {
            "customer_id": customer_id,
            "approval": False,
            "interest_rate": interest_rate,
            "tenure": tenure,
            "message": "monthly installment greater than customers monthly salary",
        }

    return {
        "customer_id": customer_id,
        "approval": True,
        "interest_rate": interest_rate,
        "corrected_interest_rate": corrected_interest_rate,
        "tenure": tenure,
        "monthly_installment": round(monthly_installment, 2),
    }


def calculate_monthly_installment(loan_amount, tenure, interest_rate):
    """
    EMI = P x R x (1+R)^N
          ------------------
           [(1+R)^N-1]
    Where:
    P: is the principal loan amount
    N: is the loan tenure in months
    R: is the monthly interest rate
    """
    # Convert annual interest rate to monthly interest rate
    monthly_interest_rate = interest_rate / 12 / 100

    # Calculate the denominator [(1+R)^N - 1]
    denominator = ((1 + monthly_interest_rate) ** tenure) - 1

    # Calculate the numerator P x R x (1+R)^N
    numerator = (
        loan_amount * monthly_interest_rate * ((1 + monthly_interest_rate) ** tenure)
    )

    # Calculate the monthly installment
    monthly_installment = numerator / denominator

    return monthly_installment


@api_view(["POST"])
def create_loan(request):
    data = request.data
    errors = {}

    customer_id = data.get("customer_id")
    if customer_id is None:
        errors["customer_id"] = "Customer ID is required."
    elif not isinstance(customer_id, int):
        errors["customer_id"] = "Customer ID must be an integer."

    loan_amount = data.get("loan_amount")
    if loan_amount is None:
        errors["loan_amount"] = "Loan amount is required."
    elif not isinstance(loan_amount, (int, float)):
        errors["loan_amount"] = "Loan amount must be a numeric value."
    elif loan_amount <= 0:
        errors["loan_amount"] = "Loan amount must be greater than zero."

    interest_rate = data.get("interest_rate")
    if interest_rate is None:
        errors["interest_rate"] = "Interest rate is required."
    elif not isinstance(interest_rate, (int, float)):
        errors["interest_rate"] = "Interest rate must be a numeric value."
    elif interest_rate <= 0:
        errors["interest_rate"] = "Interest rate must be greater than zero."

    tenure = data.get("tenure")
    if tenure is None:
        errors["tenure"] = "Tenure is required."
    elif not isinstance(tenure, int):
        errors["tenure"] = "Tenure must be an integer."
    elif tenure <= 0:
        errors["tenure"] = "Tenure must be greater than zero."

    # Check if any errors occurred
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    decide_loan_response = decide_loan_eligibility(
        customer_id, loan_amount, interest_rate, tenure
    )
    monthly_installment = decide_loan_response.get("monthly_installment")
    approval = decide_loan_response["approval"]
    if approval:
        # if eligible for loan

        loan_id = generate_unique_loan_id()

        date_of_approval = timezone.now().date()
        print(date_of_approval, "date_of_approval")

        end_date = date_of_approval + relativedelta(months=tenure)

        # Create the Loan object
        loan = Loan.objects.create(
            customer_id=customer_id,
            loan_id=loan_id,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=interest_rate,
            monthly_payment=monthly_installment,
            emis_paid_on_time=0,
            date_of_approval=date_of_approval,
            end_date=end_date,
        )

        created_loan_id = loan.loan_id
        resp = {
            "loan_id": created_loan_id,
            "customer_id": customer_id,
            "loan_approved": True,
            "monthly_installment": decide_loan_response["monthly_installment"],
        }
        return Response(resp)
    else:
        return Response(
            {
                "loan_id": None,
                "customer_id": customer_id,
                "loan_approved": False,
                "message": decide_loan_response["message"],
            }
        )


def generate_unique_loan_id():
    while True:
        loan_id = randint(1000, 9999)
        if not Loan.objects.filter(loan_id=loan_id).exists():
            return loan_id


@api_view(["GET"])
def get_loan_details_by_loan_id(request, loan_id):
    try:
        loan = Loan.objects.get(loan_id=loan_id)
        customer = Customer.objects.get(customer_id=loan.customer_id)
        monthly_installment = calculate_monthly_installment(
            loan.loan_amount, loan.tenure, loan.interest_rate
        )
        response_data = {
            "loan_id": loan.loan_id,
            "customer": {
                "customer_id": customer.customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "age": customer.age,
                "phone_number": customer.phone_number,
            },
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": round(monthly_installment, 2),
            "tenure": loan.tenure,
        }

        return Response(response_data)

    except Loan.DoesNotExist:
        return Response(
            {"message": f"Loan {loan_id} not found"}, status=status.HTTP_404_NOT_FOUND
        )

    except Customer.DoesNotExist:
        return Response(
            {"message": f"Customer not found for Loan {loan_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )

    except Exception as e:
        return Response(
            {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_loan_details_by_customer_id(request, customer_id):
    loans = Loan.objects.filter(customer_id=customer_id)
    num_of_loans = loans.count()
    print(num_of_loans, "num of loans")
    if num_of_loans == 0:
        return Response(
            {"message": f"no loans found for customer {customer_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )
    else:
        list_of_loans = []
        for loan in loans:
            d = {}
            d["loan_id"] = loan.loan_id
            d["loan_amount"] = loan.loan_amount
            d["interest_rate"] = loan.interest_rate
            monthly_installment = calculate_monthly_installment(
                loan.loan_amount, loan.tenure, loan.interest_rate
            )
            d["monthly_installment"] = round(monthly_installment, 2)
            print(loan.tenure, "tenure")
            print(loan.emis_paid_on_time, "paid on time")
            d["repayments_left"] = loan.tenure - loan.emis_paid_on_time
            list_of_loans.append(d)

        return Response(list_of_loans)


### additional
def calculate_interest_amount(loan_amount, interest_rate, tenure):
    """
    Interest = Principal * Rate * Time
    Where:

    Principal (P) is the loan amount,
    Rate (R) is the annual interest rate (expressed as a decimal),
    Time (T) is the loan tenure in years.

    """
    # Convert annual interest rate to decimal and tenure to years
    rate_decimal = interest_rate / 100
    time_years = tenure / 12  # Assuming tenure is provided in months

    # Calculate interest amount using the formula
    interest_amount = loan_amount * rate_decimal * time_years

    return interest_amount


@api_view(["DELETE"])
def delete_customer(request, customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {"message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND
        )

    customer.delete()
    return Response(
        {"message": "Customer deleted successfully"}, status=status.HTTP_204_NO_CONTENT
    )
