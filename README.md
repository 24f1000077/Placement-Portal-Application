# MAD2-placement-portal-application

Web-based Placement Portal Application (PPA) built using Flask, VueJS, and SQLite for the MAD-2 Project, with Redis for caching and Redis+Celery for background jobs. Implements role-based access for Admin, Company, and Student with placement-drive, application-pipeline, interview, and offer/placement management features.

---

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [Login Credentials](#login-credentials)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Features](#features)
- [Issues & Challenges Faced](#issues--challenges-faced)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Node.js 22.x or higher, with npm
- Redis server (used for both API caching and the Celery task queue)
- pip (Python package manager)
- Git

### Step-by-Step Guide

#### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd PMS
```

#### Step 2: Create & Activate a Virtual Environment

```bash
# From the project root
python -m venv .venv
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

> **Note:** You should see `(.venv)` at the beginning of your terminal prompt when activated.

#### Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- Flask-SQLAlchemy (database ORM)
- Flask-JWT-Extended (JWT-based authentication)
- Flask-Mail (outgoing notification emails)
- Flask-Caching (Redis-backed response caching)
- Flask-Cors (cross-origin requests from the Vue dev server)
- Celery (background/scheduled jobs)
- redis (Redis client, shared by caching, Celery, and live-update pub/sub)
- python-dotenv (environment variables)

#### Step 4: (Optional) Configure Environment Variables

Create a `backend/.env` file if you want to override any default:

```
SECRET_KEY=...
JWT_SECRET_KEY=...
DATABASE_URL=sqlite:///placementpro.db
CACHE_REDIS_URL=redis://localhost:6379/2
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=placementpro@placement.com
ADMIN_EMAIL=admin@placement.com
ADMIN_PASSWORD=admin
CORS_ORIGINS=http://localhost:5173
```

> **Note:** Every value has a working local default in `config.py`, so the app runs out of the box without a `.env` file at all.

#### Step 5: Start Redis

```bash
redis-server
```

Required before starting the backend, since caching, Celery, and the live status-update stream all depend on it.

#### Step 6: Run the Flask Backend (Creates Database, Branches & Admin)

**Option A: Using Flask CLI**
```bash
flask run
```

**Option B: Using Python directly**
```bash
python app.py
```

When the Flask app starts, it automatically:
- Creates the database (`instance/placementpro.db`)
- Creates the single Admin account (email: `admin@placement.com`, password: `admin`)
- Seeds the 8 default academic branches (Computer Science, Information Technology, Electronics & Communication, Electrical Engineering, Mechanical Engineering, Civil Engineering, Chemical Engineering, Biotechnology)

#### Step 7: Start the Celery Worker (Required for Reminders, Reports & CSV Export)

In a separate terminal, with the virtual environment active:

```bash
cd backend
celery -A celery_workers.celery worker --beat --loglevel=info
```

> **Windows:** add `--pool=solo`, e.g. `celery -A celery_workers.celery worker --beat --loglevel=info --pool=solo`.

This runs both the worker (executes jobs) and the beat scheduler (fires the daily-reminder and monthly-report jobs on schedule) in one process, which is enough for local demos.

#### Step 8: (Optional) Add Dummy Data

```bash
python seed.py
```

This populates the database with:
- 7 Company accounts across every approval status (approved, pending, rejected, blacklisted)
- 10 Student accounts across every branch and CGPA range, including one blacklisted account
- Placement drives across every status (pending, approved, applications-closed, cancelled, rejected)
- Applications across every pipeline stage (applied, shortlisted, interview, offer, rejected, withdrawn, placed), an upcoming interview, and back-dated June 2026 data for testing the monthly report job

> **Note:** The seed script does NOT delete existing data. It only adds new records, and is safe to re-run.

#### Step 9: Install & Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Step 10: Access the Application

Open your browser and navigate to:

```
http://localhost:5173
```

**Additional run options:**
```bash
flask run --port 5001      # Run the backend on a different port
flask run --debug          # Auto-reload on code changes
npm run dev -- --port 5174 # Run the frontend on a different port
```

> **Local email testing:** `MAIL_SERVER`/`MAIL_PORT` default to `localhost:1025`. Run a local debug SMTP server (e.g. MailHog) on that port to see reminder/report emails, or leave it unset — sends will simply fail and be logged to the `NotificationLog` table without breaking the app.

---

## Login Credentials

### Admin Account
| Email | Password |
|-------|----------|
| admin@placement.com | admin |

> Seeded automatically on first run from `ADMIN_EMAIL`/`ADMIN_PASSWORD`. There is no admin registration route — this is the only way an Admin account is created.

### Company Accounts (from `seed.py`)
| Email | Password | Company | Industry | Approval Status |
|-------|----------|---------|----------|-----------------|
| company1@placement.com | company1 | Acme Corp | Software | Approved |
| company2@placement.com | company2 | Beta Inc | Finance | Approved |
| company3@placement.com | company3 | Gamma Tech | Analytics | Pending |
| company4@placement.com | company4 | Delta Systems | Hardware | Rejected |
| company5@placement.com | company5 | Epsilon Labs | Biotech | Blacklisted |
| company6@placement.com | company6 | A-Systems | IT | Pending |
| company7@placement.com | company7 | EdTech Foundation | IT | Pending |

### Student Accounts (from `seed.py`)
| Email | Password | Name | Branch | CGPA | Grad. Year | Status |
|-------|----------|------|--------|------|-----------|--------|
| student1@placement.com | student1 | Aarav Shah | Computer Science | 8.7 | 2027 | Approved |
| student2@placement.com | student2 | Diya Mehta | Information Technology | 7.9 | 2027 | Approved |
| student3@placement.com | student3 | Kabir Rao | Computer Science | 6.8 | 2028 | Approved |
| student4@placement.com | student4 | Isha Nair | Electronics & Communication | 9.1 | 2027 | Approved |
| student5@placement.com | student5 | Vivaan Gupta | Mechanical Engineering | 7.2 | 2028 | Approved |
| student6@placement.com | student6 | Ananya Iyer | Computer Science | 8.3 | 2026 | Approved |
| student7@placement.com | student7 | Reyansh Joshi | Electrical Engineering | 6.5 | 2028 | Approved |
| student8@placement.com | student8 | Myra Verma | Information Technology | 8.9 | 2027 | Approved |
| student9@placement.com | student9 | Arjun Desai | Civil Engineering | 7.5 | 2028 | Approved |
| student10@placement.com | student10 | Sara Khan | Computer Science | 7.0 | 2027 | Blacklisted |

> Password for every seeded Company/Student account is the local part of its email (e.g. `student1@placement.com` → `student1`).

---

## Project Structure

```
PMS/
├── backend/                     # Flask backend application
│   ├── app.py                   # Flask app factory; creates tables, seeds branches & admin on startup
│   ├── config.py                # Database, Redis, Celery, JWT, and mail configuration
│   ├── models.py                # SQLAlchemy database models and relationships
│   ├── serializers.py           # Converts models into JSON-ready dicts for API responses
│   ├── services/                # Flask Blueprints, one per role
│   │   ├── auth.py              # Registration, login, branches, /me
│   │   ├── admin.py             # Admin routes: companies, drives, applications, students, interviews
│   │   ├── company.py           # Company routes: drives, applications, interviews, profile
│   │   └── student.py           # Student routes: drives, applications, profile, CSV export, live events
│   ├── realtime.py              # Publishes application-status change events to Redis pub/sub
│   ├── tasks.py                 # Celery background tasks (reminders, monthly report, CSV export)
│   ├── celery_workers.py        # Celery app, broker/backend config, and beat schedule
│   ├── utils.py                 # Auth decorators, password-change helper, error helper
│   ├── seed.py                  # Database seeding script for demo data
│   ├── requirements.txt         # Python dependencies for the backend
│   └── instance/                # SQLite database storage
└── frontend/                     # Vue 3 + Vite Single Page Application (UI)
    ├── src/
    │   ├── components/shared/   # Reusable UI: layout, header, modals, badges, pipeline graph
    │   ├── views/
    │   │   ├── public/           # Login, student/company registration
    │   │   ├── admin/            # Admin dashboard pages
    │   │   ├── company/          # Company dashboard pages
    │   │   └── student/          # Student dashboard pages
    │   ├── router/               # Vue Router config with role-based route guards
    │   ├── services/api.js       # Axios instance with JWT bearer-token interceptor
    │   ├── utils/                # auth store, debounce, date formatting, file download, live events
    │   ├── App.vue                # Root Vue component
    │   └── main.js                # Vue application entry point
    ├── package.json               # Node dependencies and npm scripts
    └── vite.config.js             # Vite bundler + dev-server API proxy configuration
```

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Flask** | Core backend web framework and REST API |
| **SQLite** | Lightweight local database for storing all application data |
| **Flask-SQLAlchemy** | Object Relational Mapper for the SQLite database |
| **Flask-JWT-Extended** | JWT-based authentication and role-based access control |
| **Vue 3 + Vue Router** | Reactive frontend and client-side routing |
| **Bootstrap 5** | Frontend styling and responsive layout (desktop + mobile) |
| **Axios** | Frontend-to-backend HTTP communication |
| **Redis** | Backing store for API response caching and the live status-update stream |
| **Celery + Redis** | Background/scheduled jobs: reminders, monthly report, CSV export |
| **Flask-Mail** | Sending reminder and report emails |
| **Flask-Caching** | Redis-backed caching layer with per-key expiry |
| **Flask-Cors** | Allows the Vue dev server to call the `/api/*` routes |

---

## Features

### Authentication & Security
- Unified `User` model differentiating Admin, Company, and Student via a `role` column
- JWT-based authentication (Flask-JWT-Extended); no admin registration route — the single Admin account is seeded programmatically on first startup
- `role_required` decorator gates every route: valid JWT + matching role + a fresh `is_active` check on every request, so deactivating/blacklisting a user revokes access immediately, not just at next login
- Secure password hashing (Werkzeug) and a shared password-change helper used by both Student and Company profile updates

### Admin Features
- Dashboard with total students, approved companies, and approved placement drives
- Approve/reject company registrations; blacklist/whitelist companies (blacklisting cascades: deactivates login, cancels open drives, auto-rejects in-flight applications)
- Approve/reject/close/cancel/extend-deadline on any placement drive; can also create a pre-approved company or drive directly
- View and edit all student applications campus-wide, including directly overriding status, feedback, or offer details
- Search/filter students (branch, CGPA range, graduation year, placement status) and companies; blacklist/whitelist students (cascades to withdraw in-flight applications)
- Campus-wide interview log, editable
- Download any student's resume or any application's resume/offer-letter PDF

### Company Features
- Self-registration, held to `PENDING` until Admin approval
- Create placement drives with full eligibility criteria (CGPA, target graduation years, branches, skills, salary, deadline); new drives start `PENDING`
- Edit drives while pending/rejected, extend deadline, close, or cancel (cancelling auto-rejects in-flight applications)
- View applicants per drive, including a point-in-time profile snapshot (CGPA/skills/experience/resume as they were at apply-time) and resume download
- Shortlist candidates, schedule interviews (with date/time, interviewer, meeting link, notes), make offers (salary, joining date, offer-letter PDF), or reject at any active stage
- View/manage scheduled interviews, including a join button that opens the interview's meeting link directly
- View own profile; can self-service a password change

### Student Features
- Self-registration with branch, CGPA, graduation year, contact, skills, experience
- Edit profile, upload resume, change password
- Browse approved placement drives with search/company/skills filters and an eligible-only toggle; each drive is annotated with eligibility and human-readable ineligibility reasons (branch/year/CGPA)
- Apply to a drive with a profile-snapshot confirmation step; duplicate applications to the same drive are blocked at both the API and database level
- Track application status through a visual pipeline (Applied → Shortlisted → Interview → Offer → Placed, or Rejected/Withdrawn), view interview details and join scheduled interviews, view/download offer letters, accept an offer (finalizes a placement) or withdraw
- Live status updates: the applications list and any open application/interview detail refresh automatically the moment a company (or admin) changes something — no manual refresh needed
- Export placement application history as CSV as a background job, with progress polling and automatic download once ready

### Backend Jobs (Celery + Redis)
- **Daily reminders**: finds drives closing within 48 hours and emails every eligible student (branch/year/CGPA match) who hasn't applied yet; every send/failure is logged to `NotificationLog`
- **Monthly report**: on a schedule, emails the Admin an HTML summary of the previous month's drives conducted, applications submitted, and students placed
- **CSV export**: user-triggered async job that builds a student's placement history CSV in the background

### Real-Time Updates
- A Flask Server-Sent Events endpoint (`/api/student/events`) streams application/interview changes to a logged-in student over Redis pub/sub, so the Student dashboard updates immediately without polling or a page refresh, for as long as the Applications page is open

### Performance & Caching
- Redis-backed response caching (Flask-Caching) on the heaviest list endpoints — admin's company/drive/student lists and the student's drive list — each with a 60-second expiry
- The student drive-list cache key is scoped per-student (not just per query string), since eligibility annotations differ per student
- Every mutating endpoint clears the cache so approvals/edits are reflected immediately

### Other Core Functionalities
- Eligibility validation (branch, CGPA, graduation year) enforced before any application is accepted
- Frontend HTML5 form validation on every field, backed by matching server-side validation (email/phone regex, numeric ranges, a shared drive-payload validator)
- Single responsive UI (Bootstrap 5) for both desktop and mobile
- Complete placement history maintained per student via applications + placement records

---

## Issues & Challenges Faced


1. **Problem:** Running the backend with `python app.py` intermittently crashed every cached admin/company/student list endpoint with `AttributeError: 'Cache' object has no attribute 'app'`. **Resolution:** Running a script directly makes Python treat it as the `__main__` module. Since other files do `from app import cache`, that import re-executes `app.py` a second time under a _different_ module name, creating a second, uninitialized `Cache()` instance. Switched to `flask run` (with `FLASK_APP` set via `backend/.flaskenv`), which the Flask CLI always imports consistently as `app`, so there's only ever one `cache` instance.
    
2. **Problem:** A "Graduation Year" filter showed a list of blank, unlabeled checkboxes, and clicking any one of them selected all of them at once. **Resolution:** The shared `MultiSelectDropdown` component only recognized `string` options as plain values; a `number` (e.g. `2027`) fell through to `opt.value`/`opt.label`, both `undefined`, for every option — so all checkboxes compared equal to the same `undefined`. Fixed the component to treat any non-object primitive (string or number) as a plain value.
    
3. **Problem:** Adding required columns to existing tables (e.g. splitting `target_year` into `min_target_year`/`max_target_year`) didn't error at startup, but every drive-related request then failed with "no such column." **Resolution:** The project has no migration tool (no Alembic); `db.create_all()` only creates tables that don't exist yet — it never alters an existing table's columns. For this dev/demo setup, the fix each time was to delete the SQLite file and reseed from scratch after a schema change. A production version of this app would need real migrations.
    
4. **Problem:** Registration forms had `required`, `pattern`, and range attributes on every field, but you could submit completely empty forms without any client-side warning. **Resolution:** The `<form novalidate>` attribute disables the browser's entire constraint-validation engine — so those attributes were pure decoration. Only the backend was ever actually checking them, after a full round-trip. Removed `novalidate` so native validation runs live, and added explicit input filtering (stripping non-digits) on phone number fields, since native validation alone can't prevent bad characters from being typed.
    
5. **Problem:** After adding an admin action to blacklist a company, a company that was already logged in kept full dashboard access until their token naturally expired (up to 8 hours later). **Resolution:** JWTs are stateless and were never re-checked against the database after login. Added a live `is_active` check inside the shared `role_required` decorator so every authenticated request — not just login — re-validates the account hasn't been deactivated since the token was issued.
    
6. **Problem:** A company reviewing an applicant's CGPA/skills/resume would sometimes see different data days later for the same application, because the student had since edited their profile. **Resolution:** Application detail views were reading the student's _live_ profile instead of what was true at application time. Added a point-in-time snapshot (CGPA, skills, experience, resume) copied onto the `Application` row itself at the moment a student applies, and switched every view/download to read from that snapshot instead of the live profile.
    
7. **Problem:** Renaming a CSV export's filename in the backend Celery task had no visible effect — the browser kept saving it under the old name. **Resolution:** The actual download filename wasn't coming from the backend at all. The frontend fetches the file as a raw blob (via axios) and creates its own local object URL with a hardcoded `download` attribute on a synthetic link — this discards any filename the server suggested. Had to trace the full path (Celery task → Flask `send_file` → axios blob response → frontend download helper) and fix the filename at the actual point of control: the frontend call site.
    
8. **Problem:** Several list views had a "Newest first / Oldest first" sort control that was quietly sorting by different things — some by record-creation time, interview lists by _scheduled_ time, and two admin lists had no date field of their own to sort by at all (they silently borrowed the linked user account's registration date). **Resolution:** Audited every list against its actual schema, dropped the sort control entirely on views with no genuine date field, and relabeled the rest to say exactly what they sort by (e.g. "Latest scheduled first" instead of an ambiguous "Newest first").
    
9. **Problem:** A relative SQLite path (`sqlite:///placementpro.db`) was assumed to resolve relative to whatever directory the process was started from, raising concern that changing it would silently orphan the existing database file. **Resolution:** Verified directly rather than assuming — Flask-SQLAlchemy resolves relative SQLite paths against the Flask app's `instance_path` (an app-relative `instance/` folder), independent of the process's current working directory, so the existing data stayed exactly where expected.
    
10. **Problem:** Scripted browser logins during testing intermittently landed back on the login page even though the server had returned a successful `200` login response. **Resolution:** The token-storing logic runs asynchronously after the login POST resolves; navigating to the next page immediately after clicking "submit" sometimes raced ahead of that write, discarding the session before it was persisted. Fixed by waiting for the login response to actually complete before navigating in any automated test flow.
    
11. **Challenge:** The problem statement did not specify whether Admin, as the institute's super user, should be able to directly create student, company, and placement drive records, or only approve/reject submissions made by others. **Resolution:** Coordinated with the course TA for clarification. Confirmed this was acceptable as an additional feature, and implemented direct "Create Company" and "Create Placement Drive" actions for admins, with new records saved as already approved.
    
12. **Challenge:** The intended scope of a student's "past placement history" was ambiguous — whether it should include only applications that ended in a placement, offer, or rejection, or every application the student ever submitted. **Resolution:** Coordinated with the course TA for clarification. Confirmed the scope should be all of a student's applications, regardless of outcome. The student Applications view lists every application alongside its current pipeline status.
    
13. **Challenge:** A placement drive originally targeted a single graduation year, which incorrectly excluded eligible students graduating in adjacent years from applying. **Resolution:** Replaced the single `target_year` field with a `min_target_year`/`max_target_year` range on each drive, so a drive can target a span of graduating batches, or a single year when both bounds match.

---

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError: No module named 'flask'**
```bash
# Make sure the virtual environment is activated
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
cd backend && pip install -r requirements.txt
```

**2. Connection refused to Redis / caching or Celery not working**
```bash
# Make sure Redis is running before starting the backend or Celery
redis-server
```

**3. Reminders/reports never fire, or CSV export never finishes**
- Make sure a Celery worker (with `--beat`, or a separate `celery beat` process) is running in its own terminal — the Flask app only *enqueues* jobs, it never executes them itself.

**4. Database not found or empty**
```bash
# Run the seed script to create and populate the database
cd backend
python seed.py
```

**5. CORS error in the browser console**
- Check that `CORS_ORIGINS` in `backend/.env` (or its default) matches the URL the frontend is actually served from.

**6. Port already in use**
```bash
flask run --port 5001          # Backend on a different port
npm run dev -- --port 5174     # Frontend on a different port
```
> If you change the frontend port, update `CORS_ORIGINS` and the Vite proxy target accordingly.

**7. Emails never arrive**
- `MAIL_SERVER`/`MAIL_PORT` default to a local debug SMTP server on `localhost:1025`. Run one (e.g. MailHog) to see emails, or check the `NotificationLog` table for the logged failure reason.

---

## Documentation

| File | Description |
|------|-------------|
| `README.md` | Setup instructions, login credentials, project structure, and troubleshooting |

---

## Author

**Name:** Shreya Dnyandeep Pazare
**Roll Number:** 24f1000077
**Email:** 24f1000077@ds.study.iitm.ac.in
