# API Documentation

This document provides a concise reference for the Service Booking & Appointment Management System API.

## Base URL

- Local development: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Main entities
- Users: customers, service providers, and admins
- Services: offerings created by providers
- Availability: provider availability slots for services
- Bookings: appointments made by customers for services
- Payments: payment records for bookings
- Reviews: feedback tied to bookings and providers
- Notifications: alerts sent to users
- Coupons: discount codes that can be referenced by bookings

## Authentication

Most protected endpoints require a Bearer token.

### Login
- POST /auth/login
- Body: email, password
- Returns: access token, refresh token, and user info

### Register
- POST /auth/register
- Body: full_name, email, password, phone, address, role
- Roles supported: Customer, Service Provider, Admin

### Refresh Token
- POST /auth/refresh
- Body: refresh_token

### Profile
- GET /auth/profile
- PUT /auth/profile
- PUT /auth/change-password

## Main Endpoints

### Authentication
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /auth/register | POST | No | Create a new account |
| /auth/login | POST | No | Sign in and receive JWT tokens |
| /auth/refresh | POST | No | Refresh an access token |
| /auth/profile | GET | Yes | Get current user profile |
| /auth/profile | PUT | Yes | Update current profile |
| /auth/change-password | PUT | Yes | Change password |

### Services
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /services | POST | Yes | Create a service |
| /services | GET | Optional | List services with filters |
| /services/{service_id} | GET | Optional | Get one service |
| /services/{service_id} | PUT | Yes | Update a service |
| /services/{service_id} | DELETE | Yes | Delete a service |

### Availability
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /availability | POST | Yes | Create availability slots |
| /availability | GET | Yes | List provider availability |
| /availability/{availability_id} | PUT | Yes | Update availability |
| /availability/{availability_id} | DELETE | Yes | Delete availability |
| /availability/providers/available-slots | GET | Optional | View available slots for providers/customers |

### Bookings
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /bookings | POST | Yes | Create a booking |
| /bookings | GET | Yes | List bookings for the current user |
| /bookings/export | GET | Yes | Export bookings as CSV |
| /bookings/{booking_id} | GET | Yes | Get booking details |
| /bookings/{booking_id}/confirm | PUT | Yes | Confirm a booking |
| /bookings/{booking_id}/reject | PUT | Yes | Reject a booking |
| /bookings/{booking_id}/cancel | PUT | Yes | Cancel a booking |
| /bookings/{booking_id}/reschedule | PUT | Yes | Reschedule a booking |
| /bookings/{booking_id}/complete | PUT | Yes | Mark booking complete |

### Payments
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /payments | GET | Yes | List payments |
| /payments | POST | Yes | Create a payment |
| /payments/{payment_id} | GET | Yes | Get payment details |
| /payments/{payment_id}/refund | POST | Yes | Refund a payment |

### Reviews
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /reviews | POST | Yes | Create a review |
| /reviews/provider/{provider_id} | GET | Optional | Get reviews for a provider |
| /reviews/{review_id} | PUT | Yes | Update a review |
| /reviews/{review_id} | DELETE | Yes | Delete a review |

### Notifications
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /notifications | GET | Yes | List notifications |
| /notifications/{notification_id}/read | PUT | Yes | Mark a notification as read |

### Dashboard
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /dashboard/admin | GET | Yes | Admin dashboard summary |
| /dashboard/provider | GET | Yes | Provider dashboard summary |

### Coupons
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /coupons | POST | Yes | Create a coupon |
| /coupons | GET | Yes | List coupons |

### Users
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /users | GET | Yes | List users |
| /users/{user_id} | GET | Yes | Get user details |

### Uploads
| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| /uploads/profile-image | POST | Yes | Upload profile image |
| /uploads/service-image/{service_id} | POST | Yes | Upload service image |

## Example Request Header

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Notes

- Some endpoints use role-based access control.
- The service list endpoint uses Redis caching when available.
- The app exposes Swagger UI and ReDoc for interactive testing.
