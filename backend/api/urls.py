from django.urls import path
from api.views import (
    load_customer_data,
    load_loan_data,
    register_customer,
    delete_customer,
    check_eligibility,
    create_loan,
    get_loan_details_by_loan_id,
    get_loan_details_by_customer_id,
)


urlpatterns = [
    path("register", register_customer),
    path("check-eligibility/",check_eligibility),
    path("create-loan/",create_loan),
    path("view-loan/<int:loan_id>/",get_loan_details_by_loan_id),
    path("view-loans/<int:customer_id>/",get_loan_details_by_customer_id),
    
    # background tasks
    path("populate/loan/data", load_loan_data),
    path("populate/customer/data", load_customer_data),
    
    # additional
    path("delete/<int:customer_id>/", delete_customer),
]
