import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "it-ticket-secret-key-2026"

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

DATABASE = os.path.join(os.path.dirname(__file__), "tickets.db")

PRIORITIES = ["Critique", "Haute", "Moyenne", "Basse"]
STATUSES = ["Ouvert", "En cours", "En attente", "Résolu", "Fermé"]
CATEGORIES = ["Matériel", "Logiciel", "Réseau", "Accès / Droits", "Imprimante", "Email", "Sécurité", "Autre"]


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ouvert',
            created_by INTEGER NOT NULL,
            assigned_to INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    # Seed admin account
    existing = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not existing:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO users (username, password, full_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "Administrateur IT", "admin@entreprise.com", "admin", now),
        )
        db.execute(
            "INSERT INTO users (username, password, full_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("tech1", generate_password_hash("tech123"), "Jean Dupont", "jean.dupont@entreprise.com", "tech", now),
        )
        db.execute(
            "INSERT INTO users (username, password, full_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("user1", generate_password_hash("user123"), "Marie Martin", "marie.martin@entreprise.com", "user", now),
        )
    db.commit()
    db.close()


class User(UserMixin):
    def __init__(self, id, username, full_name, email, role):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.role = role

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_tech(self):
        return self.role in ("admin", "tech")


@login_manager.user_loader
def load_user(user_id):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if row:
        return User(row["id"], row["username"], row["full_name"], row["email"], row["role"])
    return None


def log_history(db, ticket_id, user_id, action):
    db.execute(
        "INSERT INTO history (ticket_id, user_id, action, created_at) VALUES (?, ?, ?, ?)",
        (ticket_id, user_id, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE username = ?", (request.form["username"],)).fetchone()
        if row and check_password_hash(row["password"], request.form["password"]):
            user = User(row["id"], row["username"], row["full_name"], row["email"], row["role"])
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Identifiants incorrects.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    db = get_db()
    if current_user.is_tech:
        tickets = db.execute("""
            SELECT t.*, u.full_name as creator_name, a.full_name as assignee_name
            FROM tickets t
            JOIN users u ON t.created_by = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
            ORDER BY
                CASE t.priority WHEN 'Critique' THEN 1 WHEN 'Haute' THEN 2 WHEN 'Moyenne' THEN 3 ELSE 4 END,
                t.created_at DESC
        """).fetchall()
    else:
        tickets = db.execute("""
            SELECT t.*, u.full_name as creator_name, a.full_name as assignee_name
            FROM tickets t
            JOIN users u ON t.created_by = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
            WHERE t.created_by = ?
            ORDER BY t.created_at DESC
        """, (current_user.id,)).fetchall()

    stats = {
        "total": len(tickets),
        "ouverts": sum(1 for t in tickets if t["status"] == "Ouvert"),
        "en_cours": sum(1 for t in tickets if t["status"] == "En cours"),
        "resolus": sum(1 for t in tickets if t["status"] == "Résolu"),
        "critiques": sum(1 for t in tickets if t["priority"] == "Critique" and t["status"] not in ("Résolu", "Fermé")),
    }
    return render_template("dashboard.html", tickets=tickets, stats=stats, statuses=STATUSES, priorities=PRIORITIES, categories=CATEGORIES)


# ── Tickets ───────────────────────────────────────────────────────────────────

@app.route("/ticket/new", methods=["GET", "POST"])
@login_required
def new_ticket():
    if request.method == "POST":
        db = get_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = db.execute(
            "INSERT INTO tickets (title, description, category, priority, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, 'Ouvert', ?, ?, ?)",
            (request.form["title"], request.form["description"], request.form["category"], request.form["priority"], current_user.id, now, now),
        )
        ticket_id = cur.lastrowid
        log_history(db, ticket_id, current_user.id, "Ticket créé")
        db.commit()
        flash("Ticket créé avec succès.", "success")
        return redirect(url_for("view_ticket", ticket_id=ticket_id))
    return render_template("ticket_form.html", ticket=None, priorities=PRIORITIES, categories=CATEGORIES)


@app.route("/ticket/<int:ticket_id>")
@login_required
def view_ticket(ticket_id):
    db = get_db()
    ticket = db.execute("""
        SELECT t.*, u.full_name as creator_name, a.full_name as assignee_name
        FROM tickets t
        JOIN users u ON t.created_by = u.id
        LEFT JOIN users a ON t.assigned_to = a.id
        WHERE t.id = ?
    """, (ticket_id,)).fetchone()

    if not ticket:
        flash("Ticket introuvable.", "danger")
        return redirect(url_for("dashboard"))
    if not current_user.is_tech and ticket["created_by"] != current_user.id:
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))

    comments = db.execute("""
        SELECT c.*, u.full_name as author_name, u.role as author_role
        FROM comments c JOIN users u ON c.user_id = u.id
        WHERE c.ticket_id = ? ORDER BY c.created_at
    """, (ticket_id,)).fetchall()

    history = db.execute("""
        SELECT h.*, u.full_name as actor_name
        FROM history h JOIN users u ON h.user_id = u.id
        WHERE h.ticket_id = ? ORDER BY h.created_at
    """, (ticket_id,)).fetchall()

    techs = db.execute("SELECT id, full_name FROM users WHERE role IN ('admin','tech') ORDER BY full_name").fetchall()
    return render_template("ticket_detail.html", ticket=ticket, comments=comments, history=history,
                           techs=techs, statuses=STATUSES, priorities=PRIORITIES, categories=CATEGORIES)


@app.route("/ticket/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    db = get_db()
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        flash("Ticket introuvable.", "danger")
        return redirect(url_for("dashboard"))

    can_edit = current_user.is_tech or ticket["created_by"] == current_user.id
    if not can_edit:
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "UPDATE tickets SET title=?, description=?, category=?, priority=?, updated_at=? WHERE id=?",
            (request.form["title"], request.form["description"], request.form["category"], request.form["priority"], now, ticket_id),
        )
        log_history(db, ticket_id, current_user.id, "Ticket modifié")
        db.commit()
        flash("Ticket mis à jour.", "success")
        return redirect(url_for("view_ticket", ticket_id=ticket_id))
    return render_template("ticket_form.html", ticket=ticket, priorities=PRIORITIES, categories=CATEGORIES)


@app.route("/ticket/<int:ticket_id>/update", methods=["POST"])
@login_required
def update_ticket(ticket_id):
    if not current_user.is_tech:
        flash("Accès refusé.", "danger")
        return redirect(url_for("view_ticket", ticket_id=ticket_id))
    db = get_db()
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        return redirect(url_for("dashboard"))

    new_status = request.form.get("status", ticket["status"])
    assigned_to = request.form.get("assigned_to") or None
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolved_at = now if new_status in ("Résolu", "Fermé") and ticket["status"] not in ("Résolu", "Fermé") else ticket["resolved_at"]

    changes = []
    if new_status != ticket["status"]:
        changes.append(f"Statut: {ticket['status']} → {new_status}")
    if str(assigned_to or "") != str(ticket["assigned_to"] or ""):
        changes.append("Assignation modifiée")

    db.execute(
        "UPDATE tickets SET status=?, assigned_to=?, updated_at=?, resolved_at=? WHERE id=?",
        (new_status, assigned_to, now, resolved_at, ticket_id),
    )
    for change in changes:
        log_history(db, ticket_id, current_user.id, change)
    db.commit()
    flash("Ticket mis à jour.", "success")
    return redirect(url_for("view_ticket", ticket_id=ticket_id))


@app.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    content = request.form.get("content", "").strip()
    if not content:
        flash("Le commentaire ne peut pas être vide.", "warning")
        return redirect(url_for("view_ticket", ticket_id=ticket_id))
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO comments (ticket_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
        (ticket_id, current_user.id, content, now),
    )
    db.execute("UPDATE tickets SET updated_at=? WHERE id=?", (now, ticket_id))
    log_history(db, ticket_id, current_user.id, "Commentaire ajouté")
    db.commit()
    flash("Commentaire ajouté.", "success")
    return redirect(url_for("view_ticket", ticket_id=ticket_id))


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route("/admin/users")
@login_required
def admin_users():
    if not current_user.is_admin:
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY role, full_name").fetchall()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/new", methods=["GET", "POST"])
@login_required
def admin_new_user():
    if not current_user.is_admin:
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        db = get_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            db.execute(
                "INSERT INTO users (username, password, full_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (request.form["username"], generate_password_hash(request.form["password"]),
                 request.form["full_name"], request.form["email"], request.form["role"], now),
            )
            db.commit()
            flash("Utilisateur créé.", "success")
            return redirect(url_for("admin_users"))
        except sqlite3.IntegrityError:
            flash("Ce nom d'utilisateur existe déjà.", "danger")
    return render_template("admin_user_form.html", user=None)


@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("admin_users"))
    if request.method == "POST":
        pwd = request.form.get("password", "").strip()
        if pwd:
            db.execute(
                "UPDATE users SET full_name=?, email=?, role=?, password=? WHERE id=?",
                (request.form["full_name"], request.form["email"], request.form["role"], generate_password_hash(pwd), user_id),
            )
        else:
            db.execute(
                "UPDATE users SET full_name=?, email=?, role=? WHERE id=?",
                (request.form["full_name"], request.form["email"], request.form["role"], user_id),
            )
        db.commit()
        flash("Utilisateur mis à jour.", "success")
        return redirect(url_for("admin_users"))
    return render_template("admin_user_form.html", user=user)


@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    by_status = db.execute("SELECT status, COUNT(*) as n FROM tickets GROUP BY status").fetchall()
    by_priority = db.execute("SELECT priority, COUNT(*) as n FROM tickets WHERE status NOT IN ('Résolu','Fermé') GROUP BY priority").fetchall()
    by_category = db.execute("SELECT category, COUNT(*) as n FROM tickets GROUP BY category ORDER BY n DESC").fetchall()
    return jsonify({
        "by_status": {r["status"]: r["n"] for r in by_status},
        "by_priority": {r["priority"]: r["n"] for r in by_priority},
        "by_category": {r["category"]: r["n"] for r in by_category},
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
