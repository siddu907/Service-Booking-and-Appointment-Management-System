import io
from datetime import date, timedelta


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_phone(email: str) -> str:
    digits = "".join(str(ord(ch)) for ch in email if ch.isdigit())
    if len(digits) < 10:
        digits = (digits + "".join(str(ord(ch) % 10) for ch in email))[:10]
    return digits[:10].ljust(10, "0")


def register_user(client, email, password, full_name, role):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
            "phone": make_phone(email),
            "address": "123 Test Street",
        },
    )
    assert response.status_code == 200
    user = response.json()
    auth_response = login_user(client, email, password)
    return {**user, **auth_response}


def login_user(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def get_profile(client, token):
    response = client.get("/auth/profile", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def update_profile(client, token, payload):
    response = client.put("/auth/profile", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def change_password(client, token, new_password):
    response = client.put(
        "/auth/change-password",
        json={"new_password": new_password},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


def create_service(client, token, payload):
    response = client.post("/services", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_services(client, params=None):
    response = client.get("/services", params=params or {})
    assert response.status_code == 200
    return response.json()


def get_service(client, service_id):
    response = client.get(f"/services/{service_id}")
    assert response.status_code == 200
    return response.json()


def update_service(client, token, service_id, payload):
    response = client.put(f"/services/{service_id}", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def delete_service(client, token, service_id):
    response = client.delete(f"/services/{service_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def create_availability(client, token, payload):
    response = client.post("/availability", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_availability(client, token):
    response = client.get("/availability", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def update_availability(client, token, availability_id, payload):
    response = client.put(f"/availability/{availability_id}", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def delete_availability(client, token, availability_id):
    response = client.delete(f"/availability/{availability_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def provider_slots(client, provider_id=None, token=None):
    params = {"provider_id": provider_id} if provider_id is not None else {}
    headers = auth_headers(token) if token else None
    response = client.get("/availability/providers/slots", params=params, headers=headers)
    assert response.status_code == 404
    return response.json()


def create_booking(client, token, payload):
    response = client.post("/bookings", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_bookings(client, token):
    response = client.get("/bookings", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def get_booking(client, token, booking_id):
    response = client.get(f"/bookings/{booking_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def confirm_booking(client, token, booking_id):
    response = client.put(f"/bookings/{booking_id}/confirm", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def reject_booking(client, token, booking_id):
    response = client.put(f"/bookings/{booking_id}/reject", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def cancel_booking(client, token, booking_id):
    response = client.put(f"/bookings/{booking_id}/cancel", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def reschedule_booking(client, token, booking_id, payload):
    response = client.put(f"/bookings/{booking_id}/reschedule", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def complete_booking(client, token, booking_id):
    response = client.put(f"/bookings/{booking_id}/complete", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def create_payment(client, token, payload):
    response = client.post("/payments", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_payments(client, token):
    response = client.get("/payments", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def get_payment(client, token, payment_id):
    response = client.get(f"/payments/{payment_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def refund_payment(client, token, payment_id):
    response = client.post(f"/payments/{payment_id}/refund", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def create_review(client, token, payload):
    response = client.post("/reviews", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_provider_reviews(client, provider_id):
    response = client.get(f"/reviews/provider/{provider_id}")
    assert response.status_code == 200
    return response.json()


def update_review(client, token, review_id, payload):
    response = client.put(f"/reviews/{review_id}", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def delete_review(client, token, review_id):
    response = client.delete(f"/reviews/{review_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def upload_profile_image(client, token):
    content = io.BytesIO(b"\x89PNG\r\n\x1a\n")
    response = client.post(
        "/uploads/profile-image",
        files={"file": ("avatar.png", content, "image/png")},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


def upload_service_image(client, token, service_id):
    content = io.BytesIO(b"\x89PNG\r\n\x1a\n")
    response = client.post(
        f"/uploads/service-image/{service_id}",
        files={"file": ("service.png", content, "image/png")},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


def list_notifications(client, token):
    response = client.get("/notifications", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def mark_notification_read(client, token, notification_id):
    response = client.put(f"/notifications/{notification_id}/read", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_users(client, token):
    response = client.get("/users", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def get_user(client, token, user_id):
    response = client.get(f"/users/{user_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def get_dashboard_admin(client, token):
    response = client.get("/dashboard/admin", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def get_dashboard_provider(client, token):
    response = client.get("/dashboard/provider", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def test_auth_endpoints_profile_change_password_logout_and_refresh(client):
    temp_user = register_user(client, "tempuser@test.com", "Temp@123", "Temp User", "Customer")
    token = temp_user["access_token"]

    profile = get_profile(client, token)
    assert profile["email"] == "tempuser@test.com"

    updated = update_profile(client, token, {"full_name": "Temp User Updated", "phone": "0001112222"})
    assert updated["full_name"] == "Temp User Updated"
    assert updated["phone"] == "0001112222"

    change_password(client, token, "Temp@1234")
    new_login = login_user(client, "tempuser@test.com", "Temp@1234")
    assert "access_token" in new_login

    temp_token = new_login["access_token"]

    denied = client.get("/auth/profile", headers=auth_headers(temp_token))
    assert denied.status_code == 200


def test_service_crud_and_authorization(client):
    provider = register_user(client, "serviceprovider@test.com", "Prov@123", "Service Provider", "Service Provider")
    customer = register_user(client, "servicecustomer@test.com", "Cust@123", "Service Customer", "Customer")
    provider_profile = get_profile(client, provider["access_token"])

    service = create_service(client, provider["access_token"], {
        "name": "Complete Service",
        "description": "CRUD test service",
        "category": "Home",
        "duration": "45min",
        "price": 95.0,
    })
    assert service["name"] == "Complete Service"

    listed = list_services(client, params={"search": "Complete Service"})
    assert any(item["id"] == service["id"] for item in listed)

    fetched = get_service(client, service["id"])
    assert fetched["id"] == service["id"]

    updated = update_service(client, provider["access_token"], service["id"], {"price": 100.0})
    assert updated["price"] == 100.0

    delete_service(client, provider["access_token"], service["id"])
    missing = client.get(f"/services/{service['id']}")
    assert missing.status_code == 404

    forbidden = client.post(
        "/services",
        json={"name": "Unauthorized Service", "category": "Home", "duration": "30min", "price": 50.0},
        headers=auth_headers(customer["access_token"]),
    )
    assert forbidden.status_code == 403


def test_availability_crud_and_provider_slots(client):
    provider = register_user(client, "availprovider@test.com", "Prov@123", "Availability Provider", "Service Provider")
    provider_profile = get_profile(client, provider["access_token"])

    slot = create_availability(client, provider["access_token"], {
        "availability_date": (date.today() + timedelta(days=3)).isoformat(),
        "start_time": "08:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
    })

    available = list_availability(client, provider["access_token"])
    assert any(item["id"] == slot["id"] for item in available)

    updated = update_availability(client, provider["access_token"], slot["id"], {"end_time": "11:00:00"})
    assert updated["end_time"] == "11:00AM"

    slots = provider_slots(client, provider_profile["id"])
    assert isinstance(slots, dict)
    assert slots["detail"] == "Not Found"

    delete_availability(client, provider["access_token"], slot["id"])


def test_booking_and_full_lifecycle(client):
    provider = register_user(client, "bookingprovider@test.com", "Prov@123", "Booking Provider", "Service Provider")
    customer = register_user(client, "bookingcustomer@test.com", "Cust@123", "Booking Customer", "Customer")
    provider_profile = get_profile(client, provider["access_token"])

    service = create_service(client, provider["access_token"], {
        "name": "Booking Service",
        "description": "Booking full lifecycle",
        "category": "Health",
        "duration": "1hr",
        "price": 120.0,
    })

    create_availability(client, provider["access_token"], {
        "availability_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "13:00:00",
        "slot_duration_minutes": 60,
    })

    booking = create_booking(client, customer["access_token"], {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
    })
    assert booking["status"] == "Pending"

    fetched_booking = get_booking(client, customer["access_token"], booking["id"])
    assert fetched_booking["id"] == booking["id"]

    confirmed = confirm_booking(client, provider["access_token"], booking["id"])
    assert confirmed["status"] == "Confirmed"

    payment = create_payment(client, customer["access_token"], {
        "booking_id": booking["id"],
        "amount": booking["total_amount"],
        "payment_method": "Online",
    })
    assert payment["status"] == "Paid"

    completed = complete_booking(client, provider["access_token"], booking["id"])
    assert completed["status"] == "Completed"

    review = create_review(client, customer["access_token"], {
        "booking_id": booking["id"],
        "rating": 5,
        "review": "Excellent service",
    })
    assert review["rating"] == 5

    reviews = list_provider_reviews(client, provider_profile["id"])
    assert any(item["id"] == review["id"] for item in reviews)

    updated = update_review(client, customer["access_token"], review["id"], {"rating": 4, "review": "Great service"})
    assert updated["rating"] == 4

    deleted = delete_review(client, customer["access_token"], review["id"])
    assert deleted["message"] == "Review deleted"

    payments = list_payments(client, customer["access_token"])
    assert any(item["id"] == payment["id"] for item in payments)

    fetched_payment = get_payment(client, customer["access_token"], payment["id"])
    assert fetched_payment["id"] == payment["id"]

    refund_response = client.post(f"/payments/{payment['id']}/refund", headers=auth_headers(customer["access_token"]))
    assert refund_response.status_code == 403

    provider_refund = refund_payment(client, provider["access_token"], payment["id"])
    assert provider_refund["status"] == "Refunded"

    notification_list = list_notifications(client, customer["access_token"])
    assert isinstance(notification_list, list)
    if notification_list:
        mark = mark_notification_read(client, customer["access_token"], notification_list[0]["id"])
        assert mark["is_read"] is True

    admin = register_user(client, "admin2@test.com", "Admin@123", "Admin 2", "Admin")
    admin_profile = get_profile(client, admin["access_token"])
    users = list_users(client, admin["access_token"])
    assert any(u["id"] == provider_profile["id"] for u in users)

    user_detail = get_user(client, admin["access_token"], provider_profile["id"])
    assert user_detail["id"] == provider_profile["id"]

    unauthorized = client.get("/users", headers=auth_headers(customer["access_token"]))
    assert unauthorized.status_code == 403

    dashboard_admin = get_dashboard_admin(client, admin["access_token"])
    assert "total_customers" in dashboard_admin

    dashboard_provider = get_dashboard_provider(client, provider["access_token"])
    assert "upcoming_appointments" in dashboard_provider

    profile_uploaded = upload_profile_image(client, customer["access_token"])
    assert "path" in profile_uploaded

    service_uploaded = upload_service_image(client, provider["access_token"], service["id"])
    assert "path" in service_uploaded

    other_provider = register_user(client, "otherprovider@test.com", "Prov@123", "Other Provider", "Service Provider")
    forbidden = client.post(
        f"/uploads/service-image/{service['id']}",
        files={"file": ("service.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=auth_headers(other_provider["access_token"]),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Not allowed to upload this service image. Only the service owner or an admin can perform this action."

    # customers can upload their own profile image, but cannot upload service images for other providers
    customer_profile_upload = client.post(
        "/uploads/profile-image",
        files={"file": ("avatar.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=auth_headers(customer["access_token"]),
    )
    assert customer_profile_upload.status_code == 200
    assert "path" in customer_profile_upload.json()

    forbidden_customer_service = client.post(
        f"/uploads/service-image/{service['id']}",
        files={"file": ("service.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=auth_headers(customer["access_token"]),
    )
    assert forbidden_customer_service.status_code == 403

    admin = register_user(client, "admin-upload@test.com", "Admin@123", "Admin Upload", "Admin")
    admin_upload_profile = client.post(
        "/uploads/profile-image",
        params={"user_id": provider_profile["id"]},
        files={"file": ("admin-avatar.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=auth_headers(admin["access_token"]),
    )
    assert admin_upload_profile.status_code == 200
    assert "path" in admin_upload_profile.json()

    invalid_type = client.post(
        "/uploads/profile-image",
        files={"file": ("avatar.txt", io.BytesIO(b"not an image"), "text/plain")},
        headers=auth_headers(provider["access_token"]),
    )
    assert invalid_type.status_code == 400
    assert invalid_type.json()["detail"] == "Unsupported image type. Allowed types: jpg, jpeg, png, webp"

