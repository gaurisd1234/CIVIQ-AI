from flask import Flask, jsonify, request, session
from flask_cors import CORS
from datetime import datetime
import os, pickle, sqlite3, logging
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("civiq")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

from database import create_tables, get_connection
from ml_models.image_validator import check_image_quality
from ml_models.text_formatter import format_official_text

# =========================================================
# INIT
# =========================================================

from flask import send_from_directory

app = Flask(__name__)

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

app.secret_key = os.environ.get("SECRET_KEY", "civiq_default_dev_secret_key_2026")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH
)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File size exceeds the 10MB limit"}), 413

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "Frontend"))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def index_page():
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    file_path = os.path.join(FRONTEND_FOLDER, filename)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_FOLDER, filename)
    return jsonify({"error": "File not found"}), 404

create_tables()

# =========================================================
# LOAD ML MODEL
# =========================================================

MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

classifier = None
vectorizer = None
model_loaded = False

try:
    with open(os.path.join(MODEL_DIR, "classifier.pkl"), "rb") as f:
        classifier = pickle.load(f)

    with open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "rb") as f:
        vectorizer = pickle.load(f)

    model_loaded = True
    logger.info("ML classifier and vectorizer successfully loaded.")
except Exception as e:
    logger.warning("Failed to load ML models from %s: %s", MODEL_DIR, str(e))
    model_loaded = False

# =========================================================
# AUTH DECORATORS
# =========================================================

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return wrapper


def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route("/ai_status")
@login_required
def ai_status():
    return jsonify({
        "status": "Online" if model_loaded else "Offline",
        "loaded": model_loaded
    })

@app.route("/authority_signup", methods=["POST"])
@app.route("/register_authority", methods=["POST"])
def authority_signup():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    department = data.get("department")

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
        INSERT INTO users (name,email,password,role,department,status,created_at)
        VALUES (?,?,?,?,?,?,?)
        """,(
            name,
            email,
            generate_password_hash(password),
            "authority",
            department,
            "active",
            datetime.now().isoformat()
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        logger.warning("Authority registration failed: email already exists for %s", email)
        return jsonify({"error": "Email already exists"}), 400
    except Exception as e:
        conn.close()
        logger.exception("Unexpected error during authority signup: %s", str(e))
        return jsonify({"error": "Registration failed"}), 500

    conn.close()

    return jsonify({"status": "authority_created"})


# =========================================================
# SIGNUP (CITIZEN)
# =========================================================

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    phone_number = data.get("phone_number") or data.get("phone")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (name,email,password,role,phone_number,status,created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (
            name,
            email,
            generate_password_hash(password),
            "citizen",
            phone_number,
            "active",
            datetime.now().isoformat()
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        logger.warning("Citizen signup failed: email already exists for %s", email)
        return jsonify({"error": "Email already exists"}), 400
    except Exception as e:
        conn.close()
        logger.exception("Unexpected error during citizen signup: %s", str(e))
        return jsonify({"error": "Signup failed"}), 500

    conn.close()

    return jsonify({"status": "signup_success"})


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    department = data.get("department")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()

    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    if user["status"] != "active":
        return jsonify({"error": "Account not approved"}), 403

    # authority department validation
    if user["role"] == "authority":

        if user["department"] and user["department"] != department:
            return jsonify({"error": "Invalid department"}), 401

    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["name"]

    if user["role"] == "authority":
        session["department"] = user["department"]

    return jsonify({
        "status": "success",
        "role": user["role"],
        "name": user["name"]
    })


# =========================================================
# CHECK SESSION
# =========================================================

@app.route("/check_session")
def check_session():

    if "user_id" not in session:
        return jsonify({"logged_in": False})

    return jsonify({
        "logged_in": True,
        "role": session.get("role"),
        "name": session.get("name")
    })

# =========================================================
# GET CURRENT USER INFO
# =========================================================

@app.route("/user_info")
@login_required
def user_info():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id,name,email,role,department,profile_picture FROM users WHERE id=?",
        (session["user_id"],)
    )

    user = cur.fetchone()

    conn.close()

    return jsonify(dict(user))

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"status": "logged_out"})


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():

    name = request.form.get("name")
    phone = request.form.get("phone")

    image = request.files.get("profile_picture")

    conn = get_connection()
    cur = conn.cursor()

    image_name = None

    if image and image.filename:
        if not allowed_file(image.filename):
            conn.close()
            return jsonify({"error": "Invalid file type. Allowed: jpg, jpeg, png"}), 400

        safe_name = secure_filename(image.filename)
        ext = safe_name.rsplit(".", 1)[1].lower() if "." in safe_name else "jpg"
        image_name = f"profile_{session['user_id']}.{ext}"

        image.save(os.path.join(UPLOAD_FOLDER, image_name))

        cur.execute("""
        UPDATE users
        SET name=?, phone_number=?, profile_picture=?
        WHERE id=?
        """, (name, phone, image_name, session["user_id"]))

    else:

        cur.execute("""
        UPDATE users
        SET name=?, phone_number=?
        WHERE id=?
        """, (name, phone, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "profile_updated"})

# =========================================================
# SUBMIT COMPLAINT
# =========================================================

@app.route("/submit_complaint", methods=["POST"])
@login_required
@role_required("citizen")
def submit_complaint():

    text = request.form.get("complaint_text")
    severity = request.form.get("severity")
    location = request.form.get("location")
    image = request.files.get("image")

    user_id = session["user_id"]

    official_summary = format_official_text(text)

    if model_loaded and classifier and vectorizer:
        try:
            vec = vectorizer.transform([text])
            category = classifier.predict(vec)[0]
        except Exception as e:
            logger.warning("Prediction failed: %s, defaulting to 'general'", str(e))
            category = "general"
    else:
        category = "general"

    priority = {"low":1,"medium":2,"high":3}.get(severity,1)

    image_path = None
    image_valid = 0

    if image and image.filename:
        if not allowed_file(image.filename):
            return jsonify({"error": "Invalid file type. Allowed: jpg, jpeg, png"}), 400

        safe_name = secure_filename(image.filename)
        filename = f"{int(datetime.now().timestamp())}_{safe_name}"

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        image.save(filepath)

        image_path = filename

        image_valid = check_image_quality(filepath)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO complaints
        (user_id,complaint_text,category,severity,location,
        priority,support_count,status,created_at,
        image_path,image_valid,official_summary,priority_explanation)

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id,
        text,
        category,
        severity,
        location,
        priority,
        0,
        "open",
        datetime.now().isoformat(),
        image_path,
        image_valid,
        official_summary,
        f"Severity: {severity}"
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# =========================================================
# GET COMPLAINTS
# =========================================================

@app.route("/complaints")
@login_required
def get_complaints():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT complaints.*, users.name
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        ORDER BY priority DESC, created_at DESC
    """)

    rows = cur.fetchall()
    data = []

    for r in rows:
        complaint = dict(r)

        cur_comments = conn.cursor()
        cur_comments.execute("""
            SELECT comments.comment_text, users.name
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE complaint_id=?
        """, (r["id"],))

        complaint["comments"] = [dict(c) for c in cur_comments.fetchall()]
        data.append(complaint)

    conn.close()
    return jsonify({
        "data": data,
        "ai_engine": "Live" if model_loaded else "Offline",
        "model_loaded": model_loaded
    })


# =========================================================
# UPDATE STATUS
# =========================================================

@app.route("/complaints/<int:id>/status", methods=["PUT"])
@login_required
@role_required("authority")
def update_status(id):

    status = request.json.get("status")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE complaints SET status=? WHERE id=?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})


# =========================================================
# LIKE
# =========================================================

@app.route("/complaints/<int:id>/like", methods=["POST"])
@login_required
def like_complaint(id):

    user_id = session["user_id"]
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO complaint_likes (complaint_id, user_id, created_at)
            VALUES (?, ?, ?)
        """, (id, user_id, datetime.now().isoformat()))

        cur.execute(
            "UPDATE complaints SET support_count = support_count + 1 WHERE id=?",
            (id,)
        )

        conn.commit()
        conn.close()
        return jsonify({"status": "liked", "message": "Support added"})

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "You have already supported this complaint"}), 400
    except Exception as e:
        conn.close()
        logger.exception("Error adding like for complaint %s by user %s: %s", id, user_id, str(e))
        return jsonify({"error": "Failed to like complaint"}), 500

@app.route("/complaints/<int:id>/comment", methods=["POST"])
@login_required
def add_comment(id):

    data = request.get_json()
    comment_text = data.get("comment")

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO comments (complaint_id, user_id, comment_text, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        id,
        user_id,
        comment_text,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "comment_added"})


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(debug=debug_mode)