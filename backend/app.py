from flask import Flask, jsonify, request, session
from flask_cors import CORS
from datetime import datetime
import os, pickle
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from database import create_tables, get_connection
from ml_models.image_validator import check_image_quality
from ml_models.text_formatter import format_official_text

# =========================================================
# INIT
# =========================================================

from flask import send_from_directory

app = Flask(__name__)

CORS(app, supports_credentials=True, origins=r"http://.*")

app.secret_key = "super_secret_key_change_this"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

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

with open(os.path.join(MODEL_DIR, "classifier.pkl"), "rb") as f:
    classifier = pickle.load(f)

with open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "rb") as f:
    vectorizer = pickle.load(f)

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

@app.route("/authority_signup", methods=["POST"])
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

    except:

        conn.close()
        return jsonify({"error":"Email already exists"})

    conn.close()

    return jsonify({"status":"authority_created"})


# =========================================================
# SIGNUP (CITIZEN)
# =========================================================

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (name,email,password,role,status,created_at)
            VALUES (?,?,?,?,?,?)
        """, (
            name,
            email,
            generate_password_hash(password),
            "citizen",
            "active",
            datetime.now().isoformat()
        ))

        conn.commit()

    except:
        conn.close()
        return jsonify({"error": "Email already exists"}), 400

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

        image_name = f"profile_{session['user_id']}.jpg"

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

    vec = vectorizer.transform([text])
    category = classifier.predict(vec)[0]

    priority = {"low":1,"medium":2,"high":3}.get(severity,1)

    image_path = None
    image_valid = 0

    if image:

        filename = f"{int(datetime.now().timestamp())}_{image.filename}"

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
    return jsonify({"data": data})


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

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE complaints SET support_count = support_count + 1 WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "liked"})

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
# DB ADMIN API ENDPOINTS (FULL CRUD)
# =========================================================

@app.route("/api/db/tables", methods=["GET"])
def get_db_tables():
    conn = get_connection()
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';").fetchall()
    result = []
    for t in tables:
        t_name = t['name']
        columns = cur.execute(f"PRAGMA table_info('{t_name}')").fetchall()
        count = cur.execute(f"SELECT COUNT(*) as cnt FROM '{t_name}'").fetchone()['cnt']
        cols = [{"name": col['name'], "type": col['type'], "pk": col['pk']} for col in columns]
        result.append({"name": t_name, "count": count, "columns": cols})
    conn.close()
    return jsonify({"tables": result})

@app.route("/api/db/table/<table_name>", methods=["GET"])
def get_table_data(table_name):
    conn = get_connection()
    cur = conn.cursor()
    tables = [t['name'] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    if table_name not in tables:
        conn.close()
        return jsonify({"error": "Invalid table name"}), 400

    columns = [col['name'] for col in cur.execute(f"PRAGMA table_info('{table_name}')").fetchall()]
    rows = [dict(r) for r in cur.execute(f"SELECT * FROM '{table_name}';").fetchall()]
    conn.close()
    return jsonify({"columns": columns, "rows": rows})

@app.route("/api/db/table/<table_name>", methods=["POST"])
def insert_table_row(table_name):
    conn = get_connection()
    cur = conn.cursor()
    tables = [t['name'] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    if table_name not in tables:
        conn.close()
        return jsonify({"error": "Invalid table name"}), 400

    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({"error": "No data provided"}), 400

    if table_name == "users" and "password" in data and not str(data["password"]).startswith("scrypt:"):
        data["password"] = generate_password_hash(data["password"])

    cols = list(data.keys())
    vals = list(data.values())
    placeholders = ", ".join(["?"] * len(vals))
    col_str = ", ".join([f"'{c}'" for c in cols])

    try:
        cur.execute(f"INSERT INTO '{table_name}' ({col_str}) VALUES ({placeholders})", vals)
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({"status": "success", "id": new_id})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

@app.route("/api/db/table/<table_name>/<int:row_id>", methods=["PUT"])
def update_table_row(table_name, row_id):
    conn = get_connection()
    cur = conn.cursor()
    tables = [t['name'] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    if table_name not in tables:
        conn.close()
        return jsonify({"error": "Invalid table name"}), 400

    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({"error": "No data provided"}), 400

    if table_name == "users" and "password" in data and not str(data["password"]).startswith("scrypt:"):
        data["password"] = generate_password_hash(data["password"])

    set_clause = ", ".join([f"'{k}' = ?" for k in data.keys()])
    vals = list(data.values())
    vals.append(row_id)

    try:
        cur.execute(f"UPDATE '{table_name}' SET {set_clause} WHERE id=?", vals)
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

@app.route("/api/db/table/<table_name>/<int:row_id>", methods=["DELETE"])
def delete_table_row(table_name, row_id):
    conn = get_connection()
    cur = conn.cursor()
    tables = [t['name'] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    if table_name not in tables:
        conn.close()
        return jsonify({"error": "Invalid table name"}), 400

    try:
        cur.execute(f"DELETE FROM '{table_name}' WHERE id=?", (row_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

@app.route("/api/db/query", methods=["POST"])
def execute_sql_query():
    sql = request.json.get("query", "").strip()
    if not sql:
        return jsonify({"error": "Empty query"}), 400

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        if sql.lower().startswith("select"):
            rows = [dict(r) for r in cur.fetchall()]
            cols = list(rows[0].keys()) if rows else []
            conn.close()
            return jsonify({"columns": cols, "rows": rows, "count": len(rows)})
        else:
            conn.commit()
            affected = cur.rowcount
            conn.close()
            return jsonify({"status": "success", "affected_rows": affected})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)