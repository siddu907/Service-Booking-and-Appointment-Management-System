import asyncio
import io
from datetime import date, datetime, time, timedelta

import pytest

from app.background.reminder_tasks import send_upcoming_reminders
from app.database import SessionLocal
from app.models.availability import Availability
from app.models.booking import Booking
from app.routers.availability import _availability_to_response
from app.services.cache_service import CacheService
from app.services.email_service import EmailService


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
    headers = auth_headers(token) if token else None
    params = {"provider_id": provider_id} if provider_id is not None else {}
    response = client.get("/availability/providers/slots", headers=headers, params=params)
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


def approve_payment(client, token, payment_id):
    response = client.post(f"/payments/{payment_id}/approve", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_payments(client, token):
    response = client.get("/payments", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def create_coupon(client, token, payload):
    response = client.post("/coupons", json=payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def list_coupons(client, token):
    response = client.get("/coupons", headers=auth_headers(token))
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
    return response


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
    return response


def get_user(client, token, user_id):
    response = client.get(f"/users/{user_id}", headers=auth_headers(token))
    return response


def get_dashboard_admin(client, token):
    response = client.get("/dashboard/admin", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def get_dashboard_provider(client, token):
    response = client.get("/dashboard/provider", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()




@pytest.fixture(scope="function")
def setup_users(client):
    return {
        "admin": register_user(client, "admin@test.com", "Admin@123", "Admin User", "Admin"),
        "provider": register_user(client, "provider@test.com", "Provider@123", "Provider User", "Service Provider"),
        "customer": register_user(client, "customer@test.com", "Customer@123", "Customer User", "Customer"),
    }


@pytest.fixture(scope="function")
def workflow_setup(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Workflow Service",
        "description": "A service for workflow tests",
        "category": "Business",
        "duration": "1hr",
        "price": 150.0,
    })

    availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=2)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "14:00:00",
        "slot_duration_minutes": 60,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=2)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
    })

    confirmed = confirm_booking(client, provider_token, booking["id"])
    assert confirmed["status"] == "Confirmed"

    payment = create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "amount": booking["total_amount"],
        "payment_method": "Card",
    })
    assert payment["status"] == "Paid"

    completed = complete_booking(client, provider_token, booking["id"])
    assert completed["status"] == "Completed"

    review_resp = create_review(client, customer_token, {
        "booking_id": booking["id"],
        "rating": 5,
        "review": "Workflow review",
    })
    assert review_resp.status_code == 200
    review = review_resp.json()

    return {
        "service": service,
        "availability": availability,
        "booking": booking,
        "payment": payment,
        "review": review,
    }


def test_auth_profile_change_password(client):
    temp_user = register_user(client, "tempcustomer@test.com", "Temp@123", "Temp Customer", "Customer")
    token = temp_user["access_token"]

    profile = get_profile(client, token)
    assert profile["email"] == "tempcustomer@test.com"

    updated = update_profile(client, token, {"full_name": "Updated Temp Customer", "phone": "1234567890"})
    assert updated["full_name"] == "Updated Temp Customer"
    assert updated["phone"] == "1234567890"

    change_password(client, token, "Newtemp@123")
    login_user(client, "tempcustomer@test.com", "Newtemp@123")


def test_auth_change_password_requires_strong_password(client):
    temp_user = register_user(client, "tempcustomer2@test.com", "Temp@123", "Temp Customer", "Customer")
    token = temp_user["access_token"]

    response = client.put(
        "/auth/change-password",
        json={"new_password": "weak"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "Password must be at least 8 characters long" in response.json()["detail"][0]["msg"]


def test_auth_change_password_rejects_same_password(client):
    temp_user = register_user(client, "tempcustomer3@test.com", "Temp@123", "Temp Customer", "Customer")
    token = temp_user["access_token"]

    response = client.put(
        "/auth/change-password",
        json={"new_password": "Temp@123"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "New password must be different from the old password"


def test_cache_service_fallback():
    cache = CacheService()
    cache.set("bonus:test", {"value": 1}, ttl=2)
    assert cache.get("bonus:test") == {"value": 1}
    cache.delete("bonus:test")
    assert cache.get("bonus:test") is None


def test_background_reminder_sends_email_and_notification(client, setup_users):
    EmailService.clear_sent_messages()
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    booking_date = (datetime.utcnow().date() + timedelta(days=1)).isoformat()
    service = create_service(client, provider_token, {
        "name": "Reminder Service",
        "description": "Reminder service for tests",
        "category": "Business",
        "duration": "45min",
        "price": 120.0,
    })
    availability = create_availability(client, provider_token, {
        "availability_date": booking_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 60,
    })
    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": booking_date,
        "start_time": "09:00:00",
        "end_time": "10:00:00",
    })
    confirmed = confirm_booking(client, provider_token, booking["id"])
    assert confirmed["status"] == "Confirmed"

    send_upcoming_reminders()
    assert len(EmailService.sent_messages) >= 2
    notifications = list_notifications(client, customer_token)
    assert any(notification["title"] == "Appointment Reminder" for notification in notifications)


def test_coupon_duplicate_key_error_is_reported_cleanly(client, setup_users, monkeypatch):
    admin_token = setup_users["admin"]["access_token"]

    from sqlalchemy.exc import IntegrityError
    from app.repositories.coupon_repository import CouponRepository

    def fake_create(self, coupon):
        raise IntegrityError(
            statement="INSERT INTO coupons (code, ...) VALUES (...)",
            params=(),
            orig=Exception("Key (code)=(ZOM12) already exists."),
        )

    monkeypatch.setattr(CouponRepository, "create", fake_create)

    response = client.post(
        "/coupons",
        json={
            "code": "ZOM12",
            "description": "string",
            "discount_percent": 10,
            "usage_limit": 1,
        },
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Coupon code already exists"


def test_coupon_non_duplicate_db_error_is_not_reported_as_duplicate(client, setup_users, monkeypatch):
    admin_token = setup_users["admin"]["access_token"]

    from sqlalchemy.exc import IntegrityError
    from app.repositories.coupon_repository import CouponRepository

    def fake_create(self, coupon):
        raise IntegrityError(
            statement="INSERT INTO coupons (...) VALUES (...)",
            params=(),
            orig=Exception('null value in column "discount_amount" of relation "coupons" violates not-null constraint'),
        )

    monkeypatch.setattr(CouponRepository, "create", fake_create)

    response = client.post(
        "/coupons",
        json={
            "code": "FRESH2026",
            "description": "string",
            "discount_percent": 10,
            "usage_limit": 1,
        },
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to create coupon"


def test_coupon_duplicate_check_is_case_insensitive(client, setup_users):
    admin_token = setup_users["admin"]["access_token"]

    create_response = client.post(
        "/coupons",
        json={
            "code": "save25",
            "description": "lowercase seeded coupon",
            "discount_percent": 25,
            "usage_limit": 1,
        },
        headers=auth_headers(admin_token),
    )
    assert create_response.status_code == 200

    duplicate_response = client.post(
        "/coupons",
        json={
            "code": "SAVE25",
            "description": "duplicate uppercase coupon",
            "discount_percent": 30,
            "usage_limit": 1,
        },
        headers=auth_headers(admin_token),
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Coupon code already exists"


def test_coupon_creation_and_booking_discount(client, setup_users):
    admin_token = setup_users["admin"]["access_token"]
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    coupon = create_coupon(client, admin_token, {
        "code": "DISCOUNT10",
        "description": "10% off",
        "discount_percent": 10.0,
        "usage_limit": 1,
    })
    assert coupon["code"] == "DISCOUNT10"
    assert coupon["discount_percent"] == 10.0

    booking_date = (datetime.utcnow().date() + timedelta(days=5)).isoformat()
    service = create_service(client, provider_token, {
        "name": "Coupon Service",
        "description": "Service with coupon",
        "category": "Business",
        "duration": "1hr",
        "price": 200.0,
    })
    create_availability(client, provider_token, {
        "availability_date": booking_date,
        "start_time": "10:00:00",
        "end_time": "14:00:00",
        "slot_duration_minutes": 60,
    })
    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": booking_date,
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "coupon_code": "DISCOUNT10",
    })
    assert booking["original_amount"] == 200.0
    assert booking["discount_amount"] == 20.0
    assert booking["total_amount"] == 180.0
    assert booking["coupon_code"] == "DISCOUNT10"

    # Coupon should be expended after use
    response = client.post(
        "/bookings",
        json={
            "service_id": service["id"],
            "appointment_date": booking_date,
            "start_time": "11:00:00",
            "end_time": "12:00:00",
            "coupon_code": "DISCOUNT10",
        },
        headers=auth_headers(customer_token),
    )
    assert response.status_code == 400
    assert "Coupon is not active" in response.json()["detail"]


def test_booking_csv_export(client, workflow_setup, setup_users):
    customer_token = setup_users["customer"]["access_token"]
    response = client.get("/bookings/export", headers=auth_headers(customer_token))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.text
    assert "id,customer_id,service_id,provider_id,appointment_date,start_time,end_time,total_amount,status" in text
    assert str(workflow_setup["booking"]["id"]) in text


def test_service_crud_and_list(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Test Service CRUD",
        "description": "Service CRUD test",
        "category": "Home",
        "duration": "45min",
        "price": 80.0,
    })

    services = list_services(client, params={"search": "Test Service CRUD"})
    assert any(item["id"] == service["id"] for item in services)

    fetched = get_service(client, service["id"])
    assert fetched["name"] == "Test Service CRUD"

    updated = update_service(client, provider_token, service["id"], {"price": 90.0})
    assert updated["price"] == 90.0

    delete_service(client, provider_token, service["id"])
    response = client.get(f"/services/{service['id']}")
    assert response.status_code == 404

    failed = client.post("/services", json={"name": "Bad Service", "category": "Home", "duration": "30min", "price": 50.0}, headers=auth_headers(customer_token))
    assert failed.status_code == 403


def test_service_image_upload_updates_service_list(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Test Service Image",
        "description": "Service image visibility test",
        "category": "Home",
        "duration": "45min",
        "price": 80.0,
    })

    upload_service_image(client, provider_token, service["id"])

    services = list_services(client, params={"search": "Test Service Image"})
    found = next((item for item in services if item["id"] == service["id"]), None)
    assert found is not None
    assert found["service_image"] is not None

    fetched = get_service(client, service["id"])
    assert fetched["service_image"] is not None


def test_provider_sees_only_their_services_in_list(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]

    other_provider = register_user(client, "otherprovider@test.com", "Prov@123", "Other Provider", "Service Provider")
    other_provider_token = login_user(client, "otherprovider@test.com", "Prov@123")["access_token"]

    my_service = create_service(client, provider_token, {
        "name": "My Provider Scoped Service",
        "description": "Only visible to the creator",
        "category": "Home",
        "duration": "1hr",
        "price": 70.0,
    })
    other_service = create_service(client, other_provider_token, {
        "name": "Other Provider Scoped Service",
        "description": "Visible only to the other provider",
        "category": "Home",
        "duration": "1hr",
        "price": 75.0,
    })

    response = client.get("/services", headers=auth_headers(provider_token))
    assert response.status_code == 200
    services = response.json()
    assert any(item["id"] == my_service["id"] for item in services)
    assert not any(item["id"] == other_service["id"] for item in services)


def test_provider_cannot_view_another_provider_service(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    other_provider = register_user(client, "other2provider@test.com", "Prov@123", "Other2 Provider", "Service Provider")
    other_provider_token = login_user(client, "other2provider@test.com", "Prov@123")["access_token"]

    other_service = create_service(client, other_provider_token, {
        "name": "Other Provider View Test Service",
        "description": "Should not be visible to another provider",
        "category": "Home",
        "duration": "1hr",
        "price": 60.0,
    })

    response = client.get(f"/services/{other_service['id']}", headers=auth_headers(provider_token))
    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to view services owned by another provider"


def test_provider_cannot_update_another_provider_service(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    other_provider = register_user(client, "other3provider@test.com", "Prov@123", "Other3 Provider", "Service Provider")
    other_provider_token = login_user(client, "other3provider@test.com", "Prov@123")["access_token"]

    other_service = create_service(client, other_provider_token, {
        "name": "Other Provider Update Test Service",
        "description": "Should not be updatable by another provider",
        "category": "Home",
        "duration": "1hr",
        "price": 65.0,
    })

    response = client.put(
        f"/services/{other_service['id']}",
        json={"price": 70.0},
        headers=auth_headers(provider_token),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to update services owned by another provider"


def test_provider_cannot_delete_another_provider_service(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    other_provider = register_user(client, "other4provider@test.com", "Prov@123", "Other4 Provider", "Service Provider")
    other_provider_token = login_user(client, "other4provider@test.com", "Prov@123")["access_token"]

    other_service = create_service(client, other_provider_token, {
        "name": "Other Provider Delete Test Service",
        "description": "Should not be deletable by another provider",
        "category": "Home",
        "duration": "1hr",
        "price": 80.0,
    })

    response = client.delete(
        f"/services/{other_service['id']}",
        headers=auth_headers(provider_token),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to delete services owned by another provider"


def test_provider_cannot_create_availability_for_past_date(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]

    response = client.post(
        "/availability",
        json={
            "availability_date": (date.today() - timedelta(days=1)).isoformat(),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "slot_duration_minutes": 30,
        },
        headers=auth_headers(provider_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Availability date cannot be in the past. Please select today or a future date."


def test_availability_crud_and_provider_slots(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    provider_profile = get_profile(client, provider_token)

    slot = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=3)).isoformat(),
        "start_time": "08:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
    })

    available = list_availability(client, provider_token)
    assert any(item["id"] == slot["id"] for item in available)

    updated = update_availability(client, provider_token, slot["id"], {"end_time": "11:00:00"})
    assert updated["end_time"] == "11:00AM"


    delete_availability(client, provider_token, slot["id"])


def test_create_availability_returns_service_id_and_service_name(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    service = create_service(client, provider_token, {
        "name": "Service Output Test",
        "description": "Service for availability output test",
        "category": "Home",
        "duration": "45min",
        "price": 55.0,
    })

    slot = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=2)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
        "service_id": service["id"],
    })

    assert slot["service_id"] == service["id"]
    assert slot["service_name"] == service["name"]

    delete_availability(client, provider_token, slot["id"])


def test_service_provider_sees_only_own_availability_slots(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    other_provider = register_user(client, "otherprovider2@test.com", "Prov@123", "Other Provider", "Service Provider")
    other_provider_token = login_user(client, "otherprovider2@test.com", "Prov@123")["access_token"]

    other_slot = create_availability(client, other_provider_token, {
        "availability_date": (date.today() + timedelta(days=5)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
    })

    response = client.get("/availability/providers/slots", headers=auth_headers(provider_token))
    assert response.status_code == 404

    response = client.get(
        "/availability/providers/slots",
        headers=auth_headers(provider_token),
        params={"provider_id": other_provider['user']['id']},
    )
    assert response.status_code == 404

    delete_availability(client, other_provider_token, other_slot["id"])


def test_booking_and_reschedule_cancel_reject(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Booking Test Service",
        "description": "Booking test",
        "category": "Health",
        "duration": "30min",
        "price": 40.0,
    })

    availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 30,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "09:30:00",
    })

    booking_list = list_bookings(client, customer_token)
    assert any(item["id"] == booking["id"] for item in booking_list)

    fetched = get_booking(client, customer_token, booking["id"])
    assert fetched["id"] == booking["id"]

    rejected = reject_booking(client, provider_token, booking["id"])
    assert rejected["status"] == "Cancelled"

    new_booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "10:30:00",
    })
    cancelled = cancel_booking(client, customer_token, new_booking["id"])
    assert cancelled["status"] == "Cancelled"

    reschedule_booking_request = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "10:30:00",
    })
    rescheduled = reschedule_booking(client, customer_token, reschedule_booking_request["id"], {
        "appointment_date": (date.today() + timedelta(days=4)).isoformat(),
        "start_time": "11:00:00",
        "end_time": "11:30:00",
    })
    assert rescheduled["status"] == "Pending"


def test_payment_list_get_and_refund(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Payment Service",
        "description": "Payment test",
        "category": "Finance",
        "duration": "1hr",
        "price": 70.0,
    })

    availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=6)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 60,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=6)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
    })
    confirm_booking(client, provider_token, booking["id"])

    payment = create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "amount": booking["total_amount"],
        "payment_method": "Online",
    })
    assert payment["status"] == "Paid"

    payments = list_payments(client, customer_token)
    assert any(item["id"] == payment["id"] for item in payments)

    fetched = get_payment(client, customer_token, payment["id"])
    assert fetched["booking_id"] == booking["id"]

    refund_response = client.post(f"/payments/{payment['id']}/refund", headers=auth_headers(customer_token))
    assert refund_response.status_code == 403

    provider_refund = refund_payment(client, provider_token, payment["id"])
    assert provider_refund["status"] == "Refunded"


def test_payment_creation_uses_booking_total_when_amount_not_provided(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Auto Payment Service",
        "description": "Auto payment test",
        "category": "Wellness",
        "duration": "60min",
        "price": 80.0,
    })

    create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=8)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 60,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=8)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
    })
    confirm_booking(client, provider_token, booking["id"])

    payment = create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "payment_method": "UPI",
    })

    assert payment["status"] == "Paid"
    assert payment["amount"] == booking["total_amount"]


def test_cash_payment_is_marked_paid(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Cash Payment Service",
        "description": "Cash payment test",
        "category": "Wellness",
        "duration": "30min",
        "price": 40.0,
    })

    create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=9)).isoformat(),
        "start_time": "14:00:00",
        "end_time": "16:00:00",
        "slot_duration_minutes": 30,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=9)).isoformat(),
        "start_time": "14:00:00",
        "end_time": "14:30:00",
    })
    confirm_booking(client, provider_token, booking["id"])

    payment = create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "payment_method": "Cash",
    })

    assert payment["status"] == "Paid"
    assert payment["payment_method"] == "Cash"


def test_customer_cannot_book_past_time_slot(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Past Time Slot Service",
        "description": "Past time booking test",
        "category": "Wellness",
        "duration": "30min",
        "price": 50.0,
    })

    create_availability(client, provider_token, {
        "availability_date": date.today().isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
    })

    response = client.post(
        "/bookings",
        json={
            "service_id": service["id"],
            "appointment_date": date.today().isoformat(),
            "start_time": (datetime.now() - timedelta(minutes=5)).strftime("%H:%M:%S"),
            "end_time": (datetime.now() - timedelta(minutes=1)).strftime("%H:%M:%S"),
        },
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Time completed. Please select a future time slot."


def test_customer_cannot_refund_payment(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Refund Test Service",
        "description": "Refund access test",
        "category": "Wellness",
        "duration": "45min",
        "price": 60.0,
    })

    create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=10)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "slot_duration_minutes": 45,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=10)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "09:45:00",
    })
    confirm_booking(client, provider_token, booking["id"])

    payment = create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "payment_method": "Card",
    })

    response = client.post(f"/payments/{payment['id']}/refund", headers=auth_headers(customer_token))
    assert response.status_code == 403

    provider_refund = client.post(f"/payments/{payment['id']}/refund", headers=auth_headers(provider_token))
    assert provider_refund.status_code == 200

    provider_dashboard = get_dashboard_provider(client, provider_token)
    assert provider_dashboard["today_appointments"] == 0
    assert provider_dashboard["upcoming_appointments"] == 1
    assert provider_dashboard["completed_appointments"] == 0
    assert provider_dashboard["total_earnings"] == 0.0


def test_provider_dashboard_earnings_update_on_payment(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Earnings Payment Service",
        "description": "Provider earnings payment test",
        "category": "Wellness",
        "duration": "45min",
        "price": 600.0,
    })

    create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=13)).isoformat(),
        "start_time": "08:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 45,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=13)).isoformat(),
        "start_time": "08:00:00",
        "end_time": "08:45:00",
    })
    confirm_booking(client, provider_token, booking["id"])

    before_payment_dashboard = get_dashboard_provider(client, provider_token)

    create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "payment_method": "Card",
    })

    provider_dashboard = get_dashboard_provider(client, provider_token)
    assert provider_dashboard["total_earnings"] - before_payment_dashboard["total_earnings"] == 600.0


def test_provider_dashboard_earnings_drop_after_refund(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Earnings Refund Service",
        "description": "Provider earnings regression test",
        "category": "Wellness",
        "duration": "60min",
        "price": 1200.0,
    })

    create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=12)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 60,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=12)).isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
    })
    confirm_booking(client, provider_token, booking["id"])
    complete_booking(client, provider_token, booking["id"])

    before_payment_dashboard = get_dashboard_provider(client, provider_token)

    payment = create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "payment_method": "Card",
    })

    after_payment_dashboard = get_dashboard_provider(client, provider_token)
    assert after_payment_dashboard["total_earnings"] - before_payment_dashboard["total_earnings"] == 1200.0

    refund_payment(client, provider_token, payment["id"])
    after_refund = get_dashboard_provider(client, provider_token)
    assert after_refund["total_earnings"] == before_payment_dashboard["total_earnings"]


def test_dashboard_ignores_soft_deleted_bookings(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]
    admin_token = setup_users["admin"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Dashboard Soft Delete Service",
        "description": "Dashboard regression test",
        "category": "Wellness",
        "duration": "30min",
        "price": 50.0,
    })

    create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=11)).isoformat(),
        "start_time": "16:00:00",
        "end_time": "18:00:00",
        "slot_duration_minutes": 30,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=11)).isoformat(),
        "start_time": "16:00:00",
        "end_time": "16:30:00",
    })
    confirm_booking(client, provider_token, booking["id"])
    create_payment(client, customer_token, {
        "booking_id": booking["id"],
        "payment_method": "Card",
    })

    db = SessionLocal()
    try:
        db_booking = db.query(Booking).filter(Booking.id == booking["id"]).first()
        if db_booking is not None:
            db_booking.status = "Completed"
            db_booking.is_deleted = True
            db.commit()
    finally:
        db.close()

    before_admin = get_dashboard_admin(client, admin_token)
    before_provider = get_dashboard_provider(client, provider_token)

    admin_after = get_dashboard_admin(client, admin_token)
    provider_after = get_dashboard_provider(client, provider_token)

    assert admin_after["total_revenue"] == before_admin["total_revenue"]
    assert provider_after["total_earnings"] == before_provider["total_earnings"]


def test_review_list_update_and_delete(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Review Service",
        "description": "Review test",
        "category": "Wellness",
        "duration": "45min",
        "price": 55.0,
    })

    availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=7)).isoformat(),
        "start_time": "13:00:00",
        "end_time": "15:00:00",
        "slot_duration_minutes": 45,
    })

    booking = create_booking(client, customer_token, {
        "service_id": service["id"],
        "appointment_date": (date.today() + timedelta(days=7)).isoformat(),
        "start_time": "13:00:00",
        "end_time": "13:45:00",
    })
    confirm_booking(client, provider_token, booking["id"])
    payment = create_payment(client, customer_token, {"booking_id": booking["id"], "amount": booking["total_amount"], "payment_method": "Card"})
    complete_booking(client, provider_token, booking["id"])

    review_resp = create_review(client, customer_token, {"booking_id": booking["id"], "rating": 4, "review": "Good work"})
    assert review_resp.status_code == 200
    review = review_resp.json()

    provider_profile = get_profile(client, provider_token)
    reviews = list_provider_reviews(client, provider_profile["id"])
    assert any(item["id"] == review["id"] for item in reviews)

    updated_review = update_review(client, customer_token, review["id"], {"rating": 5, "review": "Excellent"})
    assert updated_review["rating"] == 5

    delete_response = delete_review(client, customer_token, review["id"])
    assert delete_response["message"] == "Review deleted"


def test_notifications_users_and_websocket(client, setup_users):
    customer_token = setup_users["customer"]["access_token"]
    admin_token = setup_users["admin"]["access_token"]

    notifications = list_notifications(client, customer_token)
    assert isinstance(notifications, list)

    if notifications:
        read_result = mark_notification_read(client, customer_token, notifications[0]["id"])
        assert read_result["is_read"] is True

    response = list_users(client, admin_token)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    users_list = response.json()
    assert users_list
    first_user_id = users_list[0]["id"]
    user_detail = get_user(client, admin_token, first_user_id)
    assert user_detail.status_code == 200
    assert user_detail.json()["id"] == first_user_id

    forbidden = list_users(client, customer_token)
    assert forbidden.status_code == 403



def test_availability_response_falls_back_for_missing_duration():
    availability = Availability(
        provider_id=1,
        availability_date=date.today(),
        start_time=datetime.strptime("09:00", "%H:%M").time(),
        end_time=datetime.strptime("10:00", "%H:%M").time(),
        slot_duration_minutes=None,
        status="available",
    )
    response = _availability_to_response(availability)
    assert response["slot_duration"] == "30min"


def test_provider_available_slots_defaults_to_30_min_when_duration_missing(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    provider_profile = get_profile(client, provider_token)

    db = SessionLocal()
    try:
        availability = Availability(
            provider_id=provider_profile["id"],
            availability_date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=None,
            status="available",
        )
        db.add(availability)
        db.commit()
        db.refresh(availability)
    finally:
        db.close()

    response = client.get(
        "/availability/providers/available-slots",
        headers=auth_headers(provider_token),
    )

    assert response.status_code == 200
    assert response.json()
    assert response.json()[0]["slot_duration"] == "30min"


def test_provider_available_slots_handles_string_duration_values(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    provider_profile = get_profile(client, provider_token)

    db = SessionLocal()
    try:
        availability = Availability(
            provider_id=provider_profile["id"],
            availability_date=date.today(),
            start_time=time(11, 0),
            end_time=time(12, 0),
            slot_duration_minutes="60",
            status="available",
        )
        db.add(availability)
        db.commit()
        db.refresh(availability)
    finally:
        db.close()

    response = client.get(
        "/availability/providers/available-slots",
        params={"availability_date": date.today().isoformat()},
        headers=auth_headers(provider_token),
    )

    assert response.status_code == 200
    assert response.json()
    assert any(item["slot_duration"] == "1hr" for item in response.json())


def test_booked_slot_does_not_appear_in_public_available_slots(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    service = create_service(client, provider_token, {
        "name": "Booked Slot Service",
        "description": "Service for booking slot visibility",
        "category": "Wellness",
        "duration": "30min",
        "price": 60.0,
    })

    availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
        "service_id": service["id"],
    })

    create_booking(client, customer_token, {
        "appointment_date": (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "09:30:00",
        "service_id": service["id"],
    })

    response = client.get(
        "/availability/providers/available-slots",
        params={
            "provider_id": setup_users["provider"]["user"]["id"],
            "availability_date": (date.today() + timedelta(days=1)).isoformat(),
            "service_id": service["id"],
        },
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 200
    assert not any(
        slot["start_time"] == "09:00:00" and slot["end_time"] == "09:30:00"
        for slot in response.json()
    )

    delete_availability(client, provider_token, availability["id"])


def test_default_available_slots_endpoint_hides_booked_slots_without_provider_filter(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]
    slot_date = (date.today() + timedelta(days=5)).isoformat()

    service = create_service(client, provider_token, {
        "name": "Default Slot Visibility Service",
        "description": "Service for default available-slots visibility",
        "category": "Wellness",
        "duration": "30min",
        "price": 55.0,
    })

    create_availability(client, provider_token, {
        "availability_date": slot_date,
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
        "service_id": service["id"],
    })

    create_booking(client, customer_token, {
        "appointment_date": slot_date,
        "start_time": "09:00:00",
        "end_time": "09:30:00",
        "service_id": service["id"],
    })

    response = client.get("/availability/providers/available-slots")

    assert response.status_code == 200
    assert not any(
        slot["start_time"] == "09:00:00" and slot["end_time"] == "09:30:00"
        for slot in response.json()
    )


def test_provider_available_slots_requires_matching_service_owner(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    other_provider = register_user(client, "otherproviderfilter@test.com", "Prov@123", "Other Provider", "Service Provider")
    other_provider_token = login_user(client, "otherproviderfilter@test.com", "Prov@123")["access_token"]

    other_service = create_service(client, other_provider_token, {
        "name": "Other Provider Service",
        "description": "Used for service-based availability checks",
        "category": "Home",
        "duration": "1hr",
        "price": 90.0,
    })

    response = client.get(
        "/availability/providers/available-slots",
        params={"service_id": other_service["id"]},
        headers=auth_headers(provider_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Service does not belong to the current provider"


def test_provider_slots_show_today_and_future_dates_only(client, setup_users):
    provider_profile = get_profile(client, setup_users["provider"]["access_token"])
    provider_token = setup_users["provider"]["access_token"]
    customer_token = setup_users["customer"]["access_token"]

    db = SessionLocal()
    try:
        past_availability = Availability(
            provider_id=provider_profile["id"],
            availability_date=(date.today() - timedelta(days=1)),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=30,
            status="available",
        )
        db.add(past_availability)
        db.commit()
        db.refresh(past_availability)
    finally:
        db.close()

    today_availability = create_availability(client, provider_token, {
        "availability_date": date.today().isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "slot_duration_minutes": 30,
    })
    future_availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "11:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 30,
    })

    response = provider_slots(client, provider_profile["id"], customer_token)
    assert response["detail"] == "Not Found"

    delete_availability(client, provider_token, today_availability["id"])
    delete_availability(client, provider_token, future_availability["id"])


def test_provider_available_slots_returns_provider_and_service_metadata(client, setup_users):
    provider_token = setup_users["provider"]["access_token"]
    provider_profile = get_profile(client, provider_token)

    service = create_service(client, provider_token, {
        "name": "Metadata Slot Service",
        "description": "Service for available slot metadata",
        "category": "Wellness",
        "duration": "30min",
        "price": 70.0,
    })

    availability = create_availability(client, provider_token, {
        "availability_date": (date.today() + timedelta(days=2)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "slot_duration_minutes": 30,
        "service_id": service["id"],
    })

    response = client.get(
        "/availability/providers/available-slots",
        params={
            "service_id": service["id"],
            "availability_date": (date.today() + timedelta(days=2)).isoformat(),
        },
        headers=auth_headers(provider_token),
    )

    assert response.status_code == 200
    assert response.json()
    slot = response.json()[0]
    assert slot["provider_id"] == provider_profile["id"]
    assert slot["provider_name"] == provider_profile["full_name"]
    assert slot["service_id"] == service["id"]
    assert slot["service_name"] == service["name"]
    assert slot["availability_date"] == availability["availability_date"]

    delete_availability(client, provider_token, availability["id"])


def test_customer_cannot_search_past_dates_for_available_slots(client, setup_users):
    customer_token = setup_users["customer"]["access_token"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    response = client.get(
        "/availability/providers/available-slots",
        params={"availability_date": yesterday},
        headers=auth_headers(customer_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Customers cannot search past dates"


def test_endpoint_coverage_for_missing_routes(client, setup_users):
    provider_profile = get_profile(client, setup_users["provider"]["access_token"])
    response = client.get(f"/availability/providers/{provider_profile['id']}/slots")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
