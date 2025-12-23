from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Створюємо Flask-застосунок
# Flask "слухає" браузер і відправляє сторінки
app = Flask(__name__)

# ---------- DATABASE ----------
# Функція для підключення до бази SQLite
def get_db():
    # sqlite3.connect підключається до файлу database.db
    # row_factory дозволяє звертатися до стовпців за іменем
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Ініціалізація бази даних
def init_db():
    conn = get_db()
    # Створюємо таблицю careers, якщо її ще немає
    conn.execute("""
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT,         
            description TEXT,   
            skills TEXT,        
            level TEXT,         
            salary TEXT         
        )
    """)
    # Створюємо таблицю comments для коментарів
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            career_id INTEGER,   
            text TEXT
        )
    """)
    conn.commit()  # зберігаємо зміни
    conn.close()   # закриваємо базу

# ---------- ROUTES ----------
# Головна сторінка: список вакансій
@app.route("/")
def index():
    search = request.args.get("search", "")  # зчитуємо параметр пошуку з URL
    level = request.args.get("level", "")    # фільтр по рівню

    conn = get_db()
    sql = "SELECT * FROM careers WHERE title LIKE ?"
    params = [f"%{search}%"]  # робимо пошук по назві

    if level:  # якщо обрано рівень
        sql += " AND level = ?"
        params.append(level)

    careers = conn.execute(sql, params).fetchall()  # отримуємо дані
    conn.close()

    # render_template повертає HTML сторінку
    return render_template("index.html", careers=careers)

# Сторінка окремої вакансії з коментарями
@app.route("/career/<int:id>", methods=["GET", "POST"])
def career(id):
    conn = get_db()

    # Якщо відправили форму з коментарем
    if request.method == "POST":
        text = request.form["text"]
        conn.execute(
            "INSERT INTO comments (career_id, text) VALUES (?, ?)",
            (id, text)
        )
        conn.commit()

    # Отримуємо дані про вакансію
    career = conn.execute(
        "SELECT * FROM careers WHERE id = ?", (id,)
    ).fetchone()

    # Отримуємо всі коментарі до цієї вакансії
    comments = conn.execute(
        "SELECT * FROM comments WHERE career_id = ?", (id,)
    ).fetchall()

    conn.close()
    return render_template("career.html", career=career, comments=comments)

# Адмін сторінка для додавання вакансій
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Збираємо дані з форми
        data = (
            request.form["title"],
            request.form["description"],
            request.form["skills"],
            request.form["level"],
            request.form["salary"]
        )

        conn = get_db()
        conn.execute("""
            INSERT INTO careers (title, description, skills, level, salary)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()

        return redirect(url_for("index"))  # після додавання повертаємось на головну

    # Повертаємо HTML форму для додавання вакансії
    return render_template("admin.html")

# ---------- START ----------
if __name__ == "__main__":
    init_db()  # створюємо базу, якщо ще нема
    app.run(debug=True)  # запускаємо сервер Flask
