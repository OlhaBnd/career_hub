import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "0987654321"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Ініціалізація бази даних
def init_db():
    conn = get_db()

    # Таблиця вакансій
    conn.execute("""
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            skills TEXT,
            level TEXT,
            salary TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Таблиця коментарів
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            career_id INTEGER,
            text TEXT,
            author TEXT
        )
    """)

    conn.commit()
    conn.close()


# Головна сторінка
@app.route("/")
def index():
    search = request.args.get("search", "")
    level = request.args.get("level", "")

    conn = get_db()
    sql = "SELECT * FROM careers WHERE title LIKE ?"
    params = [f"%{search}%"]

    if level:
        sql += " AND level = ?"
        params.append(level)

    sql += " ORDER BY created_at DESC"

    careers = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template("index.html", careers=careers)


# Сторінка вакансії
@app.route("/career/<int:id>", methods=["GET", "POST"])
def career(id):
    conn = get_db()

    if request.method == "POST":
        text = request.form["text"]
        author = request.form["author"]

        conn.execute("INSERT INTO comments (career_id, text, author) VALUES (?, ?, ?)", (id, text, author))
        conn.commit()

    career = conn.execute("SELECT * FROM careers WHERE id = ?", (id,)).fetchone()

    comments = conn.execute("SELECT * FROM comments WHERE career_id = ?", (id,)).fetchall()

    conn.close()
    return render_template("career.html", career=career, comments=comments)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["user"] = "admin"
            flash("Ви успішно увійшли як адміністратор!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Невірний логін або пароль!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        data = (
            request.form["title"],
            request.form["description"],
            request.form["skills"],
            request.form["level"],
            request.form["salary"],
        )

        conn = get_db()
        conn.execute(
            """
            INSERT INTO careers (title, description, skills, level, salary, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """,
            data,
        )
        conn.commit()
        conn.close()
        flash("Вакансію успішно додано!")
        return redirect(url_for("index"))

    return render_template("admin.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
def edit_career(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        skills = request.form["skills"]
        level = request.form["level"]
        salary = request.form["salary"]

        conn.execute(
            """
            UPDATE careers 
            SET title = ?, description = ?, skills = ?, level = ?, salary = ?
            WHERE id = ?
        """,
            (title, description, skills, level, salary, id),
        )
        conn.commit()
        conn.close()
        flash("Вакансію успішно оновлено!")
        return redirect(url_for("index"))

    # Отримуємо дані вакансії для заповнення форми
    career = conn.execute("SELECT * FROM careers WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("edit_career.html", career=career)


@app.route("/admin/delete/<int:id>")
def delete_career(id):
    if "user" not in session:  # Захист
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM careers WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/admin/delete_comment/<int:id>")
def delete_comment(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    # Дізнаємося career_id, щоб після видалення повернутися на ту саму сторінку
    comment = conn.execute("SELECT career_id FROM comments WHERE id = ?", (id,)).fetchone()

    if comment:
        career_id = comment["career_id"]
        conn.execute("DELETE FROM comments WHERE id = ?", (id,))
        conn.commit()
        flash("Коментар видалено.")
        return redirect(url_for("career", id=career_id))

    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
