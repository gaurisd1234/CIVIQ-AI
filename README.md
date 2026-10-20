# CIVIQ-AI: Civic Intelligence & Complaint Management Platform

CIVIQ-AI is a web-based civic issue reporting and management platform designed to bridge the gap between citizens and municipal authorities. Citizens can report civic issues (potholes, garbage, water leaks, drainage), provide location details, upload proof images, and interact with community reports. Municipal authorities can view prioritized work queues, update issue resolution statuses, and visualize reported problems on a ward map.

---

## Current Architecture & Implementation Reality

CIVIQ-AI is built using Flask, SQLite3, and Vanilla JavaScript with Scikit-learn for text classification.

### Features Currently Implemented
1. **User Authentication & Role Management**:
   - Separate portals for Citizens and Municipal Authorities.
   - Password hashing with `werkzeug.security` (scrypt).
   - Session-based cookie authentication with `@login_required` and `@role_required` access guards.
2. **Citizen Complaint Filing**:
   - Issue text description, severity rating (`low`, `medium`, `high`), ward location, and optional image proof upload.
   - Automatic classification into categories (`garbage`, `drainage`, `road`, `streetlight`, `water`, `other`) using TF-IDF vectorization and Logistic Regression.
   - Formatted official complaint summary generation.
   - Image proof validation (sanitized filenames via `secure_filename`, allowed extensions `jpg`, `jpeg`, `png`, and a 10MB upload limit).
3. **Community Feed & Engagement**:
   - Citizens can view community complaints and threaded comments.
   - Support ("Like") counter with duplicate protection: one user can support an issue only once via the `complaint_likes` database table.
4. **Authority Dashboard**:
   - Prioritized work queue sorted by priority and submission date.
   - Real-time resolution status updates (`open`, `in_progress`, `closed`).
   - Dynamic AI Engine Status indicator verifying live classifier availability.
   - Leaflet.js interactive map plotting pinned complaint locations for predefined wards (`Ward-1` through `Ward-4`).

### Honest Scope & Limitations
- **NLP Classifier**: The active classifier in `backend/ml_models/train_model.py` is trained on an initial demonstration set of 8 curated civic complaint examples. It provides working baseline predictions but will require continuous retraining on larger, diverse complaint datasets for production use.
- **Priority Scoring**: Priority is currently mapped directly from the citizen-selected severity (`low` &rarr; 1, `medium` &rarr; 2, `high` &rarr; 3). Community support counts do not yet dynamically shift priority rankings.
- **Deduplication**: Duplicate detection algorithm (cosine similarity / semantic embeddings) is not yet active; duplicates are prevented only for user likes.

---

## Directory Structure

```
CIVIQ-AI/
├── Frontend/                           # Web user interface
│   ├── index.html                      # Public portal landing page
│   ├── citizen.html                    # Citizen portal & complaint submission
│   ├── citizen_login.html              # Citizen login
│   ├── signup.html                     # Citizen registration
│   ├── authority.html                  # Municipal authority dashboard
│   ├── authority_login.html            # Authority login
│   ├── authority_signup.html           # Authority registration
│   ├── profile.html                    # User profile view and edit
│   ├── script.js                       # Frontend API logic and UI rendering
│   └── style.css                       # Global design system
├── backend/                            # Flask backend application
│   ├── app.py                          # Flask app entry point and API routes
│   ├── civiq.db                        # SQLite database
│   ├── database.py                     # SQLite schema initialization
│   ├── ml_models/                      # Active machine learning models
│   │   ├── train_model.py              # Model training script
│   │   ├── classifier.pkl              # Pickled LogisticRegression model
│   │   ├── vectorizer.pkl              # Pickled TfidfVectorizer
│   │   ├── text_formatter.py           # Text formatting utility
│   │   └── image_validator.py          # Image validation utility
│   └── uploads/                        # User-uploaded proof images and avatars
├── data/
│   └── complaints.csv                  # Demonstration dataset
├── .env.example                        # Template for environment variables
├── requirements.txt                    # Pinned Python package dependencies
└── README.md                           # Project documentation
```

---

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.12)
- **Modern Web Browser**: Chrome, Edge, Firefox, or Safari

---

## Installation & Setup

1. **Clone or Open the Repository**:
   ```bash
   cd c:\CIVIQ-AI
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and configure your secret key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```env
   SECRET_KEY=your-secure-random-secret-key-here
   FLASK_DEBUG=False
   ```

5. **Initialize Database Tables**:
   Database tables are initialized automatically when starting the backend, or can be run manually:
   ```bash
   python backend/database.py
   ```

---

## Running the Application

1. **Start the Flask Backend**:
   ```bash
   cd backend
   python app.py
   ```
   The server starts at `http://127.0.0.1:5000`.

2. **Access the Portal**:
   - Open your browser to `http://127.0.0.1:5000` (or open `Frontend/index.html`).
   - **Citizen Portal**: Register a new citizen account or login to file complaints and view community reports.
   - **Authority Portal**: Register or login as authority (select your department, e.g., `Road Maintenance`, `Water Supply`, `Sanitation`, or `Electricity`) to manage complaints and view the ward map.

---

## API Summary

| Route | Method | Access | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Public | Serves landing page (`index.html`) |
| `/signup` | `POST` | Public | Citizen registration (saves name, email, password, phone) |
| `/authority_signup` | `POST` | Public | Authority registration (name, email, password, department) |
| `/login` | `POST` | Public | User authentication and session creation |
| `/logout` | `GET` | Public | Session termination |
| `/check_session` | `GET` | Public | Checks current session status |
| `/user_info` | `GET` | Authenticated | Retrieves current logged-in user profile |
| `/update_profile` | `POST` | Authenticated | Updates user profile and avatar image |
| `/submit_complaint` | `POST` | Citizen | Submits complaint, predicts category, saves proof |
| `/complaints` | `GET` | Authenticated | Fetches all complaints, comments, and AI status |
| `/complaints/<id>/status`| `PUT` | Authority | Updates complaint status (`open`, `in_progress`, `closed`) |
| `/complaints/<id>/like` | `POST` | Authenticated | Registers user support (prevents duplicate likes) |
| `/complaints/<id>/comment`| `POST` | Authenticated | Adds comment to a complaint |
| `/ai_status` | `GET` | Authenticated | Health check for machine learning model |
| `/uploads/<filename>` | `GET` | Public | Serves uploaded proof and avatar images |

---

## License

MIT License. Designed for civic intelligence and accountable governance.
