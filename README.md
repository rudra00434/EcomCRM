# EcomCRM

<p align="center">
  <strong>An AI-augmented e-commerce CRM built for modern operations.</strong>
</p>

<p align="center">
  EcomCRM combines customer management, product catalog control, order tracking, analytics,
  revenue intelligence, Cloudinary media handling, and a Groq-powered assistant in one
  polished Django application.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-0C4B33?style=for-the-badge&logo=django&logoColor=white" alt="Django 6.0" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/Groq-AI_Assistant-F55036?style=for-the-badge" alt="Groq AI Assistant" />
  <img src="https://img.shields.io/badge/Cloudinary-Media_Storage-3448C5?style=for-the-badge" alt="Cloudinary Media Storage" />
  <img src="https://img.shields.io/badge/Render-Deploy_Ready-4D4DFF?style=for-the-badge&logo=render&logoColor=white" alt="Render Deploy Ready" />
</p>

---

## Why This Project Stands Out

EcomCRM is not a basic CRUD demo. It is a full-stack commerce operations product that was upgraded to feel production-ready across both engineering and product layers:

- Professional dashboard and UI refresh across the template layer
- Real revenue calculations powered by database records
- Groq-powered "ASK to AI" assistant grounded on app features and live CRM context
- Cloudinary-backed customer and product media storage
- Automatic media sync during Render builds for existing records
- Safe media fallback for older assets if a Cloudinary file is missing
- Render-ready deployment config with environment-based settings
- Analytics, tags, CSV import, maps, and operational workflows preserved

For recruiters, this project demonstrates product thinking, backend ownership, frontend polish, AI integration, deployment awareness, and production debugging under real constraints.

---

## Core Product Modules

| Module | What it does | Why it matters |
| --- | --- | --- |
| Dashboard | Shows customer count, order count, delivery states, recent activity, and charts | Gives operators an instant business overview |
| Customer Directory | Manages customer profiles, contact data, map coordinates, and customer order history | Keeps relationship context in one place |
| Product Catalog | Handles product creation, updates, tags, pricing, descriptions, and media | Makes inventory easier to maintain |
| Order Management | Tracks orders across Pending, Out for delivery, and Delivered | Supports fulfillment visibility |
| Analytics | Visualizes status breakdowns and order trends using real data | Helps teams spot patterns quickly |
| Revenue Intelligence | Calculates per-day revenue, best revenue day, pipeline value, and annual projection | Turns order activity into financial insight |
| ASK to AI | Answers questions about the website using feature extraction, retrieval, and grounded generation | Adds real AI product value, not just a chatbot shell |
| About and Contact Pages | Presents the platform with a more productized feel | Improves polish and presentation quality |

---

## Feature Highlights

### 1. AI Assistant That Knows The Product

The `ASK to AI` page is connected to Groq and designed as a grounded assistant, not a generic chat box.

It uses:

- query feature extraction
- retrieval over platform capabilities and live CRM signals
- grounded answer generation
- conversation history stored in session

The assistant can explain:

- how revenue is calculated
- where to manage customers, products, and orders
- what pages exist in the system
- live operational context such as customers, products, order states, and revenue snapshots

### 2. Real Revenue, Not Dummy Numbers

The revenue page is calculated from real order and product records:

- delivered orders drive realized revenue
- pending and out-for-delivery orders contribute to pipeline value
- daily revenue is grouped by order date
- annual projection is derived from year-to-date performance

### 3. Cloudinary Media Pipeline

Media handling was upgraded to support long-term hosted storage:

- customer and product images upload to Cloudinary
- existing local media is synced during deployment
- malformed Cloudinary env values are sanitized safely
- older image records can still render through a local fallback route if needed

### 4. Recruiter-Friendly Product Presentation

The UI was modernized without breaking backend behavior:

- redesigned dashboard
- upgraded customer, product, order, analytics, revenue, login, about, and contact pages
- improved footer and navbar
- consistent cards, spacing, typography, and mobile responsiveness

---

## Architecture Snapshot

```mermaid
flowchart LR
    A[User] --> B[Django Views and Templates]
    B --> C[CRM Workflows]
    C --> D[(SQLite or Postgres via DATABASE_URL)]
    C --> E[Cloudinary Media Storage]
    C --> F[Groq Ask to AI]

    subgraph CRM Workflows
        G[Customers]
        H[Products]
        I[Orders]
        J[Analytics]
        K[Revenue]
        L[Tag Import]
    end

    F --> M[Feature Extraction]
    M --> N[Context Retrieval]
    N --> O[Grounded Response]
```

---

## Tech Stack

### Backend

- Django 6
- Django ORM
- django-filter
- WhiteNoise
- gunicorn
- dj-database-url

### Frontend

- Django Templates
- HTML
- CSS
- Bootstrap 5
- Bootstrap Icons
- JavaScript
- Chart.js
- Leaflet

### Data and Storage

- SQLite for local development
- Postgres-compatible production setup through `DATABASE_URL`
- Cloudinary for hosted media storage

### AI

- Groq API
- Structured feature extraction and grounded generation

### Deployment

- Render
- `render.yaml`
- `Procfile`
- `build.sh`

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/rudra00434/EcomCRM.git
cd EcomCRM
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and update the values:

Windows:

```bash
copy .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the server

```bash
python manage.py runserver
```

The app will be available at:

```text
http://127.0.0.1:8000
```

---

## Environment Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Yes | Django secret key |
| `DJANGO_DEBUG` | Yes | Local debug toggle |
| `DJANGO_ALLOWED_HOSTS` | Yes | Allowed hosts list |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Production | Trusted CSRF origins |
| `DATABASE_URL` | Optional | External production database |
| `CLOUDINARY_URL` | Optional | Cloudinary media storage configuration |
| `CLOUDINARY_STORAGE_PREFIX` | Optional | Folder prefix in Cloudinary |
| `GROQ_API_KEY` | Optional | Enables the live Ask to AI assistant |
| `GROQ_EXTRACT_MODEL` | Optional | Model used for feature extraction |
| `GROQ_CHAT_MODEL` | Optional | Model used for grounded responses |

Cloudinary value format:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Important for Render:

- paste only the value
- do not include angle brackets
- do not wrap the value in extra quotes
- make sure it starts with `cloudinary://`

---

## Render Deployment

This repo is already prepared for Render deployment.

Included deployment files:

- [render.yaml](render.yaml)
- [build.sh](build.sh)
- [Procfile](Procfile)

Render build flow:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py sync_media_to_cloudinary
```

Recommended production setup:

1. Connect the GitHub repository to Render.
2. Use Python `3.11.9`.
3. Add `CLOUDINARY_URL`.
4. Add `GROQ_API_KEY`.
5. Add `DATABASE_URL` if you want persistent production data beyond SQLite.
6. Deploy from the `main` branch.

---

## Testing And Validation

Useful local checks:

```bash
python manage.py check
python manage.py test account
```

Current automated coverage includes:

- revenue calculations
- Ask to AI endpoints
- session reset behavior
- production media fallback behavior

---
## Demo UI/UX Screenshots of EcomCRM
![WhatsApp Image 2026-03-31 at 1 19 03 AM (1)](https://github.com/user-attachments/assets/eb1df21f-5219-4803-a857-0d0d9ac50329)
![WhatsApp Image 2026-03-31 at 12 59 16 AM](https://github.com/user-attachments/assets/90c33153-6964-45f8-a745-1d7bd9465c9c)
![WhatsApp Image 2026-03-31 at 12 59 45 AM](https://github.com/user-attachments/assets/b1b6c678-bcc6-477b-81b9-74fb6c7c47df)
![WhatsApp Image 2026-03-31 at 1 00 14 AM](https://github.com/user-attachments/assets/76f518e6-64cc-488e-82d2-23100ead979c)
![WhatsApp Image 2026-03-31 at 1 01 07 AM](https://github.com/user-attachments/assets/3e296c0d-8c79-4eea-a437-9f83b424e249)
![WhatsApp Image 2026-03-31 at 1 02 00 AM](https://github.com/user-attachments/assets/56c872d0-4774-40a8-9852-eef62f398171)
![WhatsApp Image 2026-03-31 at 1 02 35 AM](https://github.com/user-attachments/assets/f6e92d0f-4428-4e85-a2fb-9d7040f2ea30)
![WhatsApp Image 2026-03-31 at 1 03 42 AM](https://github.com/user-attachments/assets/a938c290-f96d-41c5-83c5-2e8af798c2d8)
![WhatsApp Image 2026-03-31 at 1 04 24 AM](https://github.com/user-attachments/assets/feb8b982-a6c2-4ff8-8ddd-d719ac07312a)
![WhatsApp Image 2026-03-31 at 1 25 20 AM](https://github.com/user-attachments/assets/3452496a-4a47-49fd-961b-ebb2652e8140)
![WhatsApp Image 2026-03-31 at 1 22 57 AM](https://github.com/user-attachments/assets/d13bebc1-a77e-44f2-b473-f9a5f005f245)
![WhatsApp Image 2026-03-31 at 1 24 43 AM](https://github.com/user-attachments/assets/deb8f33d-d2bc-40a6-9aaa-bd783ba0e597)

## Project Structure

```text
EcomCRM/
|-- account/
|   |-- management/
|   |-- templatetags/
|   |-- ai_assistant.py
|   |-- forms.py
|   |-- models.py
|   |-- tests.py
|   |-- urls.py
|   `-- views.py
|-- db/
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|-- static/
|-- template/
|   |-- account/
|   |-- main.html
|   `-- navbar.html
|-- build.sh
|-- Procfile
|-- render.yaml
`-- requirements.txt
```

---

## What Recruiters Can Take From This Project

This repository demonstrates the ability to:

- ship an end-to-end Django product, not just isolated pages
- design a cleaner, more professional user experience without removing business features
- integrate third-party services like Groq and Cloudinary
- debug production deployment issues and harden the app for Render
- build features around real business metrics rather than placeholder data
- preserve operational workflows while upgrading architecture and presentation

---

## Closing Note

EcomCRM is a strong portfolio project for full-stack, backend, product engineering, and AI-integrated web roles because it shows more than coding ability. It shows product judgment, system integration, deployability, UI execution, and resilience under real-world edge cases.
