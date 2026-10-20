# CIVIQ-AI: Comprehensive Technical Audit & Gap Analysis Report

**Date of Audit**: October 20, 2026  
**Auditor**: Antigravity Technical Assistant  
**Audited Platform**: CIVIQ-AI (Civic Complaint Intelligence Platform)  
**Technology Stack**: Flask, scikit-learn (TF-IDF + Logistic Regression), SQLite3, Vanilla JavaScript / HTML5 / CSS3  
**Audit Mode**: Static Code Analysis & Runtime Artifact Verification (Read-Only Audit)

---

## 1. PROJECT STRUCTURE

### 1.1 Directory Tree (2 Levels Deep) & File Purpose Matrix

```
CIVIQ-AI/
├── Frontend/                           # Client-side user interface (HTML, CSS, Vanilla JS)
│   ├── authority.html                 # Authority dashboard with complaint work queue and Leaflet map
│   ├── authority_login.html           # Login page for municipal authority personnel
│   ├── authority_signup.html          # Registration page for municipal authority personnel
│   ├── citizen.html                   # Citizen complaint filing interface and community feed
│   ├── citizen_login.html             # Login page for citizens
│   ├── db_admin.html                  # Standalone unauthenticated web GUI for raw SQLite database administration
│   ├── index.html                     # Public landing page directing users to Citizen or Authority portals
│   ├── profile.html                   # User profile view and update page (name, phone, avatar)
│   ├── script.js                      # Client-side API interaction logic, session management, and DOM rendering
│   ├── signup.html                    # Citizen account registration page
│   └── style.css                      # Global CSS design tokens, layouts, buttons, and cards
├── backend/                            # Flask application and server-side business logic
│   ├── app.py                         # Primary Flask application entry point, routing, auth, and API handlers
│   ├── civiq.db                       # Active SQLite database file storing users, complaints, and comments
│   ├── database/                      # Empty subdirectory
│   ├── database.py                    # SQLite connection initialization and table creation schemas
│   ├── ml_models/                     # Active ML model directory loaded by Flask backend
│   │   ├── classifier.pkl             # Serialized LogisticRegression model (trained on 8 hard-coded samples)
│   │   ├── image_validator.py         # Rule-based file size check (>10KB) masquerading as image validation
│   │   ├── nlp_classifier.py          # Empty placeholder file (0 bytes)
│   │   ├── text_formatter.py          # Rule-based string formatting function for "official summaries"
│   │   ├── train_model.py             # Active model training script using 8 hard-coded text tuples
│   │   └── vectorizer.pkl             # Serialized TfidfVectorizer (vocabulary size: 27)
│   └── uploads/                       # File storage directory for user avatars and complaint proof images
│       ├── 1773382483_garbage.jpg     # Sample uploaded complaint image
│       └── 1787804445_water leakage.jpg # Sample uploaded complaint image
├── data/                               # Dataset storage directory
│   └── complaints.csv                 # Unused synthetic dataset (100 rows, 4 categories)
├── models/                             # Redundant / orphaned standalone model training directory
│   ├── classifier.pkl                 # Unused LogisticRegression pickle (4 classes, default max_iter)
│   ├── train_classifier.py            # Unused training script with 8 hard-coded samples across 4 classes
│   └── vectorizer.pkl                 # Unused TfidfVectorizer pickle
├── README.md                          # Project documentation file (completely empty: 0 bytes)
├── requirements.txt                   # Unpinned Python package dependencies
├── test.http                          # HTTP test scratchpad with a single invalid endpoint call
└── venv/                              # Python virtual environment (ignored from audit)
```

---

### 1.2 Dependency List (`requirements.txt`)
Exact contents of `requirements.txt` (lines 1–9):
```text
flask
scikit-learn
pandas
numpy
tensorflow
pillow
geopy
joblib
```
*Audit Finding*:
1. Package versions are entirely unpinned, creating non-reproducible build risks across Python versions.
2. `pandas`, `numpy`, `tensorflow`, `pillow`, `geopy`, and `joblib` are **never imported or used anywhere** in the codebase.
3. Model serialization uses Python's standard library `pickle` module rather than `joblib`.

---

### 1.3 How to Run the Application
- **Entry Point**: `backend/app.py` (lines 638–639)
- **Execution Commands**:
  ```bash
  # Optional: activate virtual environment
  .\venv\Scripts\activate

  # Run Flask server
  cd backend
  python app.py
  ```
- **Runtime Configuration**:
  - Starts Flask's built-in WSGI server on `http://127.0.0.1:5000` with `debug=True` (`backend/app.py:639`).
  - Frontend static assets are served directly through Flask via catch-all routes `@app.route("/")` and `@app.route("/<path:filename>")` (`backend/app.py:41-51`), or can be opened directly as static HTML files interacting with CORS enabled on `http://127.0.0.1:5000`.

---

## 2. DATA

### 2.1 Dataset / CSV Verification
- **File Name**: `data/complaints.csv`
- **Total Lines**: 102 lines (1 header line, 100 data rows, 1 blank trailing line).
- **Column Names**: `text`, `label` (`data/complaints.csv:1`)
- **5 Sample Rows (Complaint Text Only)**:
  1. `"Garbage not collected in area 0"` (`data/complaints.csv:2`)
  2. `"Water leaking from pipe near house 0"` (`data/complaints.csv:3`)
  3. `"Pothole on main road near sector 0"` (`data/complaints.csv:4`)
  4. `"Drain overflow near school 0"` (`data/complaints.csv:5`)
  5. `"Garbage not collected in area 1"` (`data/complaints.csv:6`)

### 2.2 Dataset Usage & Current Training Mechanism
- **Is `data/complaints.csv` used?**: **NO**. The file is completely orphaned. Neither the backend application nor the training scripts reference, read, or import `data/complaints.csv`.
- **How the active model is trained**:
  The production model loaded into memory (`backend/app.py:58-64`) is trained purely on **8 hard-coded in-memory Python tuples** defined in `backend/ml_models/train_model.py:6-15`:
  ```python
  data = [
      ("Garbage dumped near residential area", "garbage"),
      ("Overflowing garbage bins causing bad smell", "garbage"),
      ("Drainage water overflowing on road", "drainage"),
      ("Blocked drainage causing flooding", "drainage"),
      ("Large potholes on main road", "road"),
      ("Street lights not working at night", "streetlight"),
      ("Water leakage from pipeline", "water"),
      ("Noise pollution late night", "other"),
  ]
  ```
  *(Note: A second orphaned training script exists in `models/train_classifier.py:6-26` with 8 hard-coded strings across 4 categories: `garbage`, `water`, `road`, `electricity`, but its artifacts in `models/` are never loaded).*

### 2.3 Complaint Categories & Sample Distribution

#### Active Production Model (`backend/ml_models/train_model.py:6-15`):
| Category | Sample Count | Percentage of Training Data |
| :--- | :--- | :--- |
| `garbage` | 2 | 25.0% |
| `drainage` | 2 | 25.0% |
| `road` | 1 | 12.5% |
| `streetlight` | 1 | 12.5% |
| `water` | 1 | 12.5% |
| `other` | 1 | 12.5% |
| **Total** | **8** | **100%** |

#### Unused Dataset (`data/complaints.csv`):
| Category | Sample Count | Nature of Data |
| :--- | :--- | :--- |
| `garbage` | 25 | Synthetic template (`"Garbage not collected in area {0..24}"`) |
| `water` | 25 | Synthetic template (`"Water leaking from pipe near house {0..24}"`) |
| `road` | 25 | Synthetic template (`"Pothole on main road near sector {0..24}"`) |
| `drainage` | 25 | Synthetic template (`"Drain overflow near school {0..24}"`) |
| **Total** | **100** | Synthetically generated variations with appended index |

---

## 3. NLP / ML PIPELINE

### 3.1 Text Preprocessing Steps
- **Cleaning**: **NOT PRESENT**. No punctuation removal, no regex filtering, no case folding (other than Scikit-learn's default internal `lowercase=True`), and no HTML or number stripping.
- **Stopwords**: Standard Scikit-learn English stopword list enabled via `TfidfVectorizer(stop_words="english")` (`backend/ml_models/train_model.py:20`). In `models/train_classifier.py:28`, `stop_words` is `None`.
- **Stemming**: **NOT PRESENT**.
- **Lemmatization**: **NOT PRESENT**.
- **Tokenization**: Default Scikit-learn word token regex `(?u)\b\w\w+\b`.
- **Text Formatter ("Official AI Summary")**: **NOT AN ML MODEL**. Handled by a pure string concatenation template in `backend/ml_models/text_formatter.py:1-15`:
  ```python
  def format_official_text(complaint_text):
      complaint_text = complaint_text.strip()
      if not complaint_text.endswith("."):
          complaint_text += "."
      official_summary = (
          "A civic issue has been officially reported. The complaint states that "
          + complaint_text[0].lower() + complaint_text[1:]
          + " Immediate action by the concerned municipal department is requested."
      )
      return official_summary
  ```
- **Image Validation ("Computer Vision")**: **NOT AN ML MODEL**. Handled by a 10-line basic file check in `backend/ml_models/image_validator.py:3-10`:
  ```python
  def check_image_quality(path):
      if not os.path.exists(path): return 0
      if not path.lower().endswith((".jpg", ".jpeg", ".png")): return 0
      if os.path.getsize(path) < 10 * 1024: return 0  # < 10 KB fails
      return 1
  ```
  No TensorFlow, PyTorch, PIL, or convolutional networks are used.

### 3.2 Feature Extraction (TF-IDF Parameters)
Configured in `backend/ml_models/train_model.py:20`:
- `ngram_range`: `(1, 1)` (unigrams only)
- `max_features`: `None` (unbounded)
- `min_df`: `1`
- `max_df`: `1.0`
- `stop_words`: `"english"`
- `lowercase`: `True`
- `norm`: `'l2'`
- `sublinear_tf`: `False`
- **Active Vocabulary Size**: Exactly **27 words** in `backend/ml_models/vectorizer.pkl`.

### 3.3 Model Architecture & Hyperparameters
Configured in `backend/ml_models/train_model.py:23`:
- **Model**: `sklearn.linear_model.LogisticRegression`
- `max_iter`: `1000`
- `C`: `1.0` (default)
- `penalty`: `'l2'` (default)
- `solver`: `'lbfgs'` (default)
- `class_weight`: `None`
- `fit_intercept`: `True`
- `multi_class`: `'auto'` / deprecated default

### 3.4 Train / Test Split
- **Method**: **NOT PRESENT**.
- **Sizes**: **NOT PRESENT**. There is zero train/test split, cross-validation, or validation holdout. 100% of the 8 hard-coded samples are fed to `model.fit()`.

### 3.5 Model Persistence & Loading
- **Serialization Library**: Standard library `pickle` (`pickle.dump` / `pickle.load`).
- **Saved Location**: `backend/ml_models/classifier.pkl` and `backend/ml_models/vectorizer.pkl` (`backend/ml_models/train_model.py:28-32`).
- **Loaded Location**: Loaded synchronously into memory on Flask application startup in `backend/app.py:58-64`:
  ```python
  MODEL_DIR = os.path.join(BASE_DIR, "ml_models")
  with open(os.path.join(MODEL_DIR, "classifier.pkl"), "rb") as f:
      classifier = pickle.load(f)
  with open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "rb") as f:
      vectorizer = pickle.load(f)
  ```

### 3.6 Evaluation Code & Results
- **Metrics**: **NOT PRESENT**.
- **Results**: **NOT PRESENT**. No evaluation scripts, classification reports, confusion matrices, or validation accuracy scores exist or are stored anywhere in the repository.

---

## 4. DUPLICATE DETECTION

- **Exact Method**: **NOT PRESENT**.
- **Algorithm / Library**: **NOT PRESENT**.
- **Similarity Measure**: **NOT PRESENT** (no cosine similarity, Levenshtein distance, Jaccard similarity, or semantic embeddings).
- **Threshold**: **NOT PRESENT**.
- **Handling of Duplicates**: **NOT PRESENT**. Duplicate complaints are neither merged, flagged, nor linked. Every submission is unconditionally inserted as a new row in the database.
  - *Proof in active database (`backend/civiq.db`)*: Complaints `id=2` and `id=3` contain the identical text `"Large potholes on main road near station"`, identical user `user_id=2`, identical category `road`, identical severity `high`, and identical priority `3`.
- **Evaluation**: **NOT PRESENT**.

---

## 5. PRIORITY SCORING

### 5.1 Exact Formula or Logic
Priority calculation contains no mathematical formula, no statistical weights, and no machine learning. It is a **hard-coded dictionary lookup** based strictly on the citizen's form submission in `backend/app.py:334`:
```python
priority = {"low": 1, "medium": 2, "high": 3}.get(severity, 1)
```
- If severity is `"low"`, `priority = 1`.
- If severity is `"medium"`, `priority = 2`.
- If severity is `"high"`, `priority = 3`.
- Any missing or unmatched severity defaults to `1`.
- The `priority_explanation` database column is hard-coded as string concatenation: `f"Severity: {severity}"` (`backend/app.py:374`).

### 5.2 Origin of Severity and Community Support
- **Severity**: Originates directly from the citizen's manual selection in an HTML dropdown `<select id="severity">` on the complaint submission form (`Frontend/citizen.html:98-106`, forwarded by `Frontend/script.js:235, 244`).
- **Community Support**: Originates from a numeric database counter column `support_count INTEGER DEFAULT 0` (`backend/database.py:87`). When a citizen clicks the `"❤️ Support"` button (`Frontend/script.js:396-398`), a POST request is sent to `/complaints/<id>/like` (`backend/app.py:451-466`), executing:
  ```sql
  UPDATE complaints SET support_count = support_count + 1 WHERE id=?
  ```
- **Critical Audit Finding**: **Community support is completely disconnected from priority scoring**. An issue with 10,000 likes will retain whatever initial priority (`1`, `2`, or `3`) was assigned at submission; the priority field is never recalculated. Furthermore, there is no user tracking on likes, allowing any single user to click the like button infinitely to inflate support counts.

---

## 6. APPLICATION FEATURES

### 6.1 Endpoints / Routes Matrix
All endpoints are defined in `backend/app.py`:

| Method | URL | Description | Auth / Role Decorator | Line Reference |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/uploads/<filename>` | Serves uploaded images (proofs & avatars) from `backend/uploads/` | None (Public) | `app.py:37-39` |
| `GET` | `/` | Serves `Frontend/index.html` landing page | None (Public) | `app.py:41-43` |
| `GET` | `/<path:filename>` | Serves static frontend HTML/JS/CSS files; returns 404 JSON if not found | None (Public) | `app.py:45-51` |
| `POST` | `/authority_signup` | Creates an authority user account (hashes password, sets role='authority') | None (Public) | `app.py:89-127` |
| `POST` | `/signup` | Creates a citizen user account (hashes password, sets role='citizen') | None (Public) | `app.py:133-170` |
| `POST` | `/login` | Validates credentials & department; sets session cookies | None (Public) | `app.py:176-220` |
| `GET` | `/check_session` | Checks session status; returns logged_in, role, name | None (Public) | `app.py:226-236` |
| `GET` | `/user_info` | Returns profile fields for the logged-in session user | `@login_required` | `app.py:242-259` |
| `GET` | `/logout` | Clears server session cookies | None (Public) | `app.py:264-268` |
| `POST` | `/update_profile` | Updates user's name, phone_number, and optional profile picture | `@login_required` | `app.py:274-312` |
| `POST` | `/submit_complaint` | Ingests complaint, predicts category, calculates priority, stores proof | `@login_required`<br>`@role_required("citizen")` | `app.py:317-380` |
| `GET` | `/complaints` | Returns all complaints + comments, ordered by priority & date | `@login_required` | `app.py:387-420` |
| `PUT` | `/complaints/<int:id>/status` | Updates complaint status (`open`, `in_progress`, `closed`) | `@login_required`<br>`@role_required("authority")` | `app.py:426-445` |
| `POST` | `/complaints/<int:id>/like` | Increments complaint support counter by 1 | `@login_required` | `app.py:451-466` |
| `POST` | `/complaints/<int:id>/comment` | Appends a comment record linked to a complaint | `@login_required` | `app.py:468-494` |
| `GET` | `/api/db/tables` | Lists all SQLite tables, row counts, and column metadata | **None (CRITICAL RISK)** | `app.py:500-513` |
| `GET` | `/api/db/table/<table_name>` | Returns all columns and rows from any specified table | **None (CRITICAL RISK)** | `app.py:515-528` |
| `POST` | `/api/db/table/<table_name>` | Inserts arbitrary row into specified table (hashes password for 'users') | **None (CRITICAL RISK)** | `app.py:529-560` |
| `PUT` | `/api/db/table/<table_name>/<int:row_id>` | Updates arbitrary table row by ID | **None (CRITICAL RISK)** | `app.py:561-590` |
| `DELETE` | `/api/db/table/<table_name>/<int:row_id>` | Deletes arbitrary table row by ID | **None (CRITICAL RISK)** | `app.py:591-608` |
| `POST` | `/api/db/query` | **Executes raw SQL query passed in JSON payload from client** | **None (CRITICAL RISK)** | `app.py:609-632` |

---

### 6.2 Database Schema
Defined in `backend/database.py:38-127`:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    phone_number TEXT,
    profile_picture TEXT DEFAULT 'default.jpg',
    status TEXT,
    created_at TEXT 
);

CREATE TABLE complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    complaint_text TEXT NOT NULL,
    category TEXT,
    severity TEXT,
    location TEXT,
    priority INTEGER DEFAULT 1,
    support_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'open',
    created_at TEXT,
    image_path TEXT,
    image_valid INTEGER DEFAULT 0,
    official_summary TEXT,
    priority_explanation TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

### 6.3 User Roles & Authentication
- **Roles in Code**:
  - `"citizen"`: Allowed to submit complaints, view feed, like issues, post comments, update profile.
  - `"authority"`: Allowed to view complaints table, update issue status, access authority dashboard.
  - `"admin"`: **NOT PRESENT as a role**. The `role` column in the database is only populated with `"citizen"` or `"authority"`. The `db_admin.html` page exists as an unauthenticated utility with no role check.
- **Authentication**:
  - Flask server-side session cookies (`session["user_id"]`, `session["role"]`, `session["name"]`).
  - Passwords hashed using `werkzeug.security.generate_password_hash` (`scrypt`) and verified with `check_password_hash` (`backend/app.py:110, 155, 196`).
  - Route guards: `@login_required` and `@role_required(role)` (`backend/app.py:70-87`).

---

### 6.4 Frontend Pages / Templates
All frontend files are static HTML/JS (not Jinja2 templates):
1. **`index.html`**: Landing page featuring platform banner, portal links for Citizen Access and Authority Access, a header link to `db_admin.html`, and dynamic navbar user profile dropdown.
2. **`citizen_login.html`**: Citizen login box with email and password fields.
3. **`signup.html`**: Citizen registration box (name, email, phone, password, confirmPassword).
4. **`citizen.html`**: Citizen portal. Contains complaint submission form (text description, severity dropdown, ward/location input, proof upload) on left; community complaint feed with like buttons, status badges, and comments section on right.
5. **`authority_login.html`**: Authority login box with email, department dropdown (`Sanitation`, `Road Maintenance`, `Water Supply`, `Electricity`), and password.
6. **`authority_signup.html`**: Authority registration form with department selection.
7. **`authority.html`**: Authority dashboard containing a Leaflet map, KPI cards, and work queue table with status update dropdowns (`open`, `in_progress`, `closed`).
8. **`profile.html`**: User profile management (avatar preview, name, phone number, disabled department for authority).
9. **`db_admin.html`**: Standalone SQLite manager GUI containing sidebar table list, table schema viewer, editable data grids, row insert/edit/delete modal, and custom SQL query runner.
10. **`style.css`**: Shared CSS variables, responsive grid styling, card shadows, and form styling.

---

### 6.5 The Dashboard (Charts & Metrics)
Located in `Frontend/authority.html:78-106`:
- **Metrics Shown**:
  1. **Total Issues**: Displays numeric count of all complaints returned by the API (`result.data.length`, `authority.html:221`).
  2. **AI Engine Status**: Displays a **hard-coded static HTML text** string `Live` (`authority.html:97`). It is not tied to any backend ping, model health check, or latency metric.
- **Charts**: **NOT PRESENT**. There are zero chart libraries (no Chart.js, D3, or ApexCharts), zero bar charts, and zero pie charts anywhere in the project.
- **Analytics Endpoint**: **NOT PRESENT**. The `/analytics` endpoint mentioned in `test.http:1` does not exist in `backend/app.py`.

---

### 6.6 Maps, Notifications, Image Uploads, and External APIs
- **Maps**:
  - Implemented via Leaflet.js v1.7.1 (`Frontend/authority.html:13, 150, 169-174`).
  - Map is initialized at hardcoded coordinates `[19.8762, 75.3433]` (Chhatrapati Sambhajinagar / Aurangabad, Maharashtra, India).
  - Titled "Ward-wise Heatmap", but is **not a heatmap**; it plots standard individual pins (`L.marker`).
  - **Coordinates are hard-coded for only 4 specific ward names** in `Frontend/authority.html:161-166`:
    ```javascript
    const wardCoords = {
      "Ward-1": [19.8762, 75.3433],
      "Ward-2": [19.8900, 75.3500],
      "Ward-3": [19.8600, 75.3300],
      "Ward-4": [19.8800, 75.3700]
    };
    ```
    If a citizen enters anything else (e.g. "Main Market", "Ward 1" without hyphen, "Sector 5"), **no marker is plotted**.
- **Notifications**: **NOT PRESENT** (no email, SMS, WebPush, or WebSocket notifications).
- **Image Uploads**: **PRESENT**.
  - Proof images: saved in `backend/uploads/` via `submit_complaint` (`backend/app.py:339-350`).
  - Profile pictures: saved in `backend/uploads/` via `update_profile` (`backend/app.py:288-293`).
- **External APIs**:
  - OpenStreetMap tile server (`tile.openstreetmap.org`)
  - CDN libraries: Leaflet (`unpkg.com`), FontAwesome (`cdnjs.cloudflare.com`), Flaticon (`cdn-icons-png.flaticon.com`), and Unsplash image in CSS hero banner (`images.unsplash.com`).
  - External AI / LLM APIs (OpenAI, Anthropic, Gemini): **NOT PRESENT**.

---

## 7. QUALITY AND GAPS

### 7.1 Hard-coded Values, Placeholders, and Demo Logic
1. **Hardcoded Flask Secret Key**: `app.secret_key = "super_secret_key_change_this"` (`backend/app.py:22`).
2. **Hardcoded 8-Sample Model Training**: Both `backend/ml_models/train_model.py:6-15` and `models/train_classifier.py:6-26` train exclusively on 8 hardcoded sentences.
3. **Fake "AI Official Summary"**: String concatenation template in `backend/ml_models/text_formatter.py:7-13` pretending to be AI summarization.
4. **Fake "AI Image Validator"**: File size check (`os.path.getsize(path) < 10 * 1024`) in `backend/ml_models/image_validator.py:8` pretending to be image quality validation.
5. **Hardcoded Ward Map Locations**: Restricted to exactly 4 strings: `"Ward-1"`, `"Ward-2"`, `"Ward-3"`, `"Ward-4"` in `Frontend/authority.html:161-166`.
6. **Hardcoded Dashboard Status**: `<h1 style="color:var(--secondary)">Live</h1>` for "AI Engine Status" in `Frontend/authority.html:97`.
7. **Empty File**: `backend/ml_models/nlp_classifier.py` is an empty 0-byte file (`backend/ml_models/nlp_classifier.py:1`).

---

### 7.2 Security, Error Handling, and Input Validation Issues

1. **CRITICAL VULNERABILITY — Unauthenticated Arbitrary SQL Execution**:
   Endpoint `POST /api/db/query` (`backend/app.py:609-632`) has **zero authentication or role check**. Any unauthenticated client or web crawler can execute arbitrary SQL:
   ```python
   @app.route("/api/db/query", methods=["POST"])
   def execute_sql_query():
       sql = request.json.get("query", "").strip()
       ...
       cur.execute(sql)  # Allows DROP TABLE, DELETE FROM users, SELECT password, etc.
   ```
2. **CRITICAL VULNERABILITY — Unauthenticated Database CRUD Endpoints**:
   Endpoints `/api/db/tables`, `/api/db/table/<table_name>` (GET, POST, PUT, DELETE) in `backend/app.py:500-608` are completely public and unauthenticated, allowing full database exfiltration and alteration through `Frontend/db_admin.html`.
3. **SQL Injection Vulnerability in Table Insertion**:
   In `backend/app.py:552`, column names are injected directly via Python f-string:
   ```python
   col_str = ", ".join([f"'{c}'" for c in cols])
   cur.execute(f"INSERT INTO '{table_name}' ({col_str}) VALUES ({placeholders})", vals)
   ```
4. **Broken Authority Registration Route (404 Bug)**:
   In `Frontend/authority_signup.html:181`, client JavaScript calls `POST http://127.0.0.1:5000/register_authority`. However, in `backend/app.py:89`, the route is defined as `@app.route("/authority_signup", methods=["POST"])`. **Authority signup from the UI is completely broken and always fails with 404 Not Found**.
5. **Dropped Form Fields**:
   In `Frontend/signup.html:123, 154`, citizen signup asks for `phone`, but `signupUser(name, email, password)` in `Frontend/script.js:69` drops the phone number. Furthermore, `backend/app.py:133-170` does not accept or store `phone_number` on signup.
6. **Insecure CORS & Session Settings**:
   `CORS(app, supports_credentials=True, origins=r"http://.*")` (`backend/app.py:20`) permits any HTTP origin with credentials. `SESSION_COOKIE_SECURE=False` (`backend/app.py:27`).
7. **Unrestricted File Uploads**:
   In `backend/app.py:341-345`, uploaded filenames are concatenated without `werkzeug.utils.secure_filename`, permitting potential path traversal or malicious file extension uploads.
8. **Silent Bare Excepts**:
   Bare `except:` blocks in `backend/app.py:119` and `backend/app.py:163` catch all system exceptions and mask underlying operational errors.

---

### 7.3 Tests
- **Status**: **NOT PRESENT**.
- There are **zero** unit tests, integration tests, or test configurations (`unittest`, `pytest`).
- The only test-related file in the project is `test.http`, which contains 3 lines with a call to `GET http://127.0.0.1:5000/analytics`—an endpoint that does not exist in the backend.

---

### 7.4 README vs. Actual Code
- **README Status**: `README.md` is **completely empty (0 bytes)**.
- **Mismatch with UI Text & Project Claims**:
  - `Frontend/index.html:190-191` claims *"automated priority ranking and ward-wise analytics"*; in reality, priority is a simple 1/2/3 mapping of citizen-selected severity, and analytics are not implemented.
  - `Frontend/authority.html:65` claims a *"Ward-wise Heatmap"*; in reality, it is standard point markers hardcoded to only 4 ward names.
  - Requirements file lists `tensorflow`, `pillow`, `pandas`, `geopy`; in reality, none of these libraries are ever imported or utilized.

---

## 8. HONEST SUMMARY

### 8.1 Implementation Status Table

| Feature | Implementation Status | Ground Truth in Code |
| :--- | :--- | :--- |
| **User Authentication (Citizen & Authority)** | **Implemented Fully** | Bcrypt password hashing (`werkzeug.security`), session cookies, and route guards working. |
| **Citizen Complaint Submission** | **Implemented Fully** | Ingests text, severity, location, and proof image; stores in SQLite. |
| **Citizen Community Feed & Comments** | **Implemented Fully** | Shows complaints, proof images, comments list, and comment form. |
| **Community Support ("Likes")** | **Partially Implemented** | Increments counter in SQLite, but allows infinite clicking with no user tracking; not connected to priority. |
| **NLP Complaint Categorization** | **Partially Implemented** | TF-IDF + LogisticRegression code executes, but trained on only 8 hardcoded sentences (27-word vocab). `complaints.csv` is ignored. |
| **Dynamic Priority Scoring** | **Partially Implemented** | No formula or algorithm; strictly a 1/2/3 dictionary lookup from citizen-selected severity dropdown. |
| **AI Official Summary** | **Partially Implemented** | Pure string concatenation wrapper; no ML or generative summarization. |
| **Image Proof Verification** | **Partially Implemented** | Purely checks if file extension is image and file size >= 10KB; no computer vision / TensorFlow. |
| **Interactive Map** | **Partially Implemented** | Leaflet map renders, but only recognizes exactly 4 hardcoded ward names; plots pins, not a heatmap. |
| **Authority Status Workflow** | **Partially Implemented** | Status update dropdown works, but authority registration from UI is broken (404), and complaints are not filtered by department. |
| **Database Administration Tool** | **Implemented Fully** *(Severe Risk)* | Full-featured SQLite GUI, but completely unauthenticated, enabling arbitrary SQL execution. |
| **Duplicate Complaint Detection** | **NOT PRESENT (Only Claimed)** | Zero code, zero similarity algorithm, zero clustering. Exact duplicates enter database unrestricted. |
| **Analytics Dashboard & Charts** | **NOT PRESENT (Only Claimed)** | Zero charts, no chart library, and `/analytics` endpoint is nonexistent. |
| **Automated Notifications (SMS/Email)** | **NOT PRESENT** | No notification dispatch logic or third-party service integration. |
| **Automated Test Suite** | **NOT PRESENT** | Zero test files exist. |

---

### 8.2 The 5 Biggest Weaknesses in the Current ML / NLP Pipeline

1. **Extreme Data Starvation & Ignored Dataset**:
   The active classifier was trained on only **8 hand-crafted sentences** (`backend/ml_models/train_model.py:6-15`), resulting in an impoverished vocabulary of just 27 terms. 4 out of the 6 classes (`road`, `streetlight`, `water`, `other`) have **only a single training sample**. The 100-row dataset in `data/complaints.csv` is completely unused. In real-world usage, any sentence containing unseen words will trigger arbitrary or default classification.
2. **Complete Absence of Model Evaluation & Validation**:
   There is **no train/test split, cross-validation, or evaluation metric** (accuracy, precision, recall, F1) anywhere in the repository. The model was evaluated on 0 test samples; its generalization error and accuracy are mathematically undefined.
3. **Total Lack of Duplicate Detection**:
   Despite deduplication being a core requirement of civic complaint platforms, there is **zero duplicate detection code** (no TF-IDF cosine similarity, no Word2Vec/BERT embeddings, and no string matching). Exact duplicate submissions are inserted without warning or clustering.
4. **Simulated / Mocked "AI" Features**:
   Both the "AI Official Summary" and "Image Quality Verification" are rule-based stubs designed to appear as AI in the UI:
   - The summary generator is a fixed 3-line string concatenation (`"A civic issue has been officially reported..."`).
   - The image validator is an `os.path.getsize(path) < 10240` byte check, despite `tensorflow` and `pillow` being listed in `requirements.txt`.
5. **No Robust NLP Preprocessing or Subword / N-gram Handling**:
   The TF-IDF vectorizer uses default `ngram_range=(1, 1)` and unstemmed tokens. It cannot capture multi-word civic terms (e.g., "street light", "water leakage", "pothole on road"), cannot process typos, and possesses no Lemmatization/Stemming pipeline to normalize complaints across tenses or pluralities.
