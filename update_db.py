import sqlite3


def migrate_db():
    conn = sqlite3.connect("database.db")

    try:
        # Додаємо колонку БЕЗ автоматичного часу (просто як текст)
        conn.execute("ALTER TABLE careers ADD COLUMN created_at TIMESTAMP")
        print("✅ Колонка 'created_at' додана.")

        # Заповнюємо вже існуючі вакансії поточною датою
        conn.execute("UPDATE careers SET created_at = datetime('now') WHERE created_at IS NULL")
        print("✅ Існуючі записи оновлені датою.")

    except sqlite3.OperationalError as e:
        print(f"ℹ️ Пропущено для 'careers': {e}")

    try:
        conn.execute("ALTER TABLE comments ADD COLUMN author TEXT")
        print("✅ Колонка 'author' додана.")
    except sqlite3.OperationalError as e:
        print(f"ℹ️ Пропущено для 'comments': {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate_db()
