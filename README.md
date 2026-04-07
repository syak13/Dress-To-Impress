# Dress To Impress

A dress rental microservices application built for IS213 (Enterprise Solution Development).

## Architecture Overview

```
Frontend (Vue 3, :5173)
    ↓
Kong API Gateway (:8000 proxy, :8001 admin)
    ↓
Composite Services
    ↓
Atomic Services + External APIs
```

### Services

| Service | Port | Type | Description |
|---|---|---|---|
| customer_service | 5000 | Atomic | Customer accounts, login, registration |
| inventory_service | 5001 | Atomic | Dress catalogue and availability |
| booking_service | 5002 | Atomic | Fitting appointment records |
| rental_service | 5004 | Atomic | Rental records and status |
| invoice_service | 5005 | Atomic | Invoices and Stripe payment intents |
| return_assessment_service | 5006 | Atomic | AI damage assessment via Groq |
| fitting_service | 5010 | Composite | Schedule/cancel fitting appointments |
| place_rental_order | 5011 | Composite | Place, confirm, and cancel rental orders |
| returning_service | 5012 | Composite | Process dress returns with AI assessment |

### External Integrations

- **Stripe** — payment processing for rentals
- **Groq** — AI vision model for dress damage assessment on return
- **Twilio (via OutSystems)** — SMS/email notifications via RabbitMQ

## Prerequisites

- Docker Desktop
- Node.js (for frontend)

## Environment Variables

Create a `.env` file in the project root:

```env
STRIPE_SECRET_KEY=sk_test_...
GROQ_API_KEY=gsk_...
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Running the App

### 1. Start all backend services

```bash
docker compose up --build
```

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Access the app

- Frontend: http://localhost:5173
- Kong Proxy: http://localhost:8000
- Kong Admin: http://localhost:8001
- phpMyAdmin: http://localhost:8080
- RabbitMQ Dashboard: http://localhost:15672

## Kong API Routes

All frontend traffic goes through Kong on port 8000:

| Path | Service | Methods |
|---|---|---|
| `/customer` | customer_service | GET, POST, PUT |
| `/fitting` | fitting_service | GET, POST, PUT |
| `/rental-order` | place_rental_order | GET, POST, PUT |
| `/return` | returning_service | GET, POST, PUT |

## User Scenarios

- **UC1/UC2a** — Browse all dresses (`GET /fitting/dresses`)
- **UC2b** — Browse available dresses (`GET /fitting/available`)
- **UC2** — Schedule a fitting (`POST /fitting/schedule`)
- **UC3** — Rent a dress (`POST /rental-order` → Stripe → `POST /rental-order/confirm`)
- **UC4** — Return a dress (`POST /return/image`)
