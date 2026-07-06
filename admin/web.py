import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from functools import wraps
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

FLASK_USERNAME = os.getenv("FLASK_USERNAME", "admin")
FLASK_PASSWORD = os.getenv("FLASK_PASSWORD", "admin123")
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/database.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if (request.form["username"] == FLASK_USERNAME and
                request.form["password"] == FLASK_PASSWORD):
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Неверный логин или пароль"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    status_filter = request.args.get("status", "")
    conn = get_connection()

    if status_filter:
        apps = conn.execute(
            "SELECT * FROM applications WHERE status=? ORDER BY created_at DESC",
            (status_filter,)
        ).fetchall()
    else:
        apps = conn.execute(
            "SELECT * FROM applications ORDER BY created_at DESC"
        ).fetchall()

    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
        "new": conn.execute("SELECT COUNT(*) FROM applications WHERE status='new'").fetchone()[0],
        "in_progress": conn.execute("SELECT COUNT(*) FROM applications WHERE status='in_progress'").fetchone()[0],
        "done": conn.execute("SELECT COUNT(*) FROM applications WHERE status='done'").fetchone()[0],
    }
    conn.close()

    return render_template("index.html", applications=apps, stats=stats, current_status=status_filter)


@app.route("/update_status", methods=["POST"])
@login_required
def update_status():
    app_id = request.form["id"]
    new_status = request.form["status"]
    status_filter = request.referrer.split("status=")[-1] if "status=" in (request.referrer or "") else ""
    conn = get_connection()
    conn.execute("UPDATE applications SET status=? WHERE id=?", (new_status, app_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index", status=status_filter))


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    app_id = request.form["id"]
    conn = get_connection()
    conn.execute("DELETE FROM applications WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for("index"))


@app.route("/export")
@login_required
def export():
    status_filter = request.args.get("status", "")
    conn = get_connection()
    if status_filter:
        rows = conn.execute(
            "SELECT * FROM applications WHERE status=? ORDER BY created_at DESC",
            (status_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY created_at DESC"
        ).fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Заявки"

    headers = ["ID", "Имя", "Возраст", "Цель", "Контакт", "Дата", "Статус"]
    header_fill = PatternFill("solid", fgColor="2C3E50")
    header_font = Font(color="FFFFFF", bold=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row in rows:
        ws.append([
            row["id"],
            row["name"],
            row["age"],
            row["goal"],
            row["contact"],
            row["created_at"][:16],
            row["status"],
        ])

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 30
    ws.column_dimensions["E"].width = 25
    ws.column_dimensions["F"].width = 18
    ws.column_dimensions["G"].width = 15

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="applications.xlsx"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)