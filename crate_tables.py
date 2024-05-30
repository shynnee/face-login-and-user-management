import sqlite3

# Kết nối đến cơ sở dữ liệu SQLite
conn = sqlite3.connect('user_data.db')
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'  
            )''')


c.execute('''CREATE TABLE IF NOT EXISTS user_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                face_image BLOB NOT NULL,
                email TEXT NOT NULL,
                address TEXT NOT NULL,
                FOREIGN KEY(username) REFERENCES users(username)
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS registration_time (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username)
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS login_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                login_count INTEGER DEFAULT 0,
                last_login_time TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username)
            )''')


conn.commit()
conn.close()

print("Tables created successfully.")
