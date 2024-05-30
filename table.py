import sqlite3
import tkinter as tk
from tkinter import ttk

def fetch_data():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    users = c.fetchall()

    c.execute('SELECT * FROM user_details')
    user_details = c.fetchall()

    c.execute('SELECT * FROM registration_time')
    registration_times = c.fetchall()

    c.execute('SELECT * FROM login_stats')
    login_stats = c.fetchall()

    conn.close()

    return users, user_details, registration_times, login_stats

def create_table(title, columns, data):
    window = tk.Toplevel()
    window.title(title)

    tree = ttk.Treeview(window, columns=columns, show='headings')

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), foreground="blue")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    for row in data:
        tree.insert("", "end", values=row)

    tree.pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    users, user_details, registration_times, login_stats = fetch_data()

    create_table('Users', ['ID', 'Full Name', 'Username', 'Password', 'Role'], users)
    create_table('User Details', ['ID', 'Username', 'Face Image', 'Email', 'Address'], user_details)
    create_table('Registration Time', ['ID', 'Username', 'Registration Time'], registration_times)
    create_table('Login Stats', ['ID', 'Username', 'Login Count', 'Last Login Time'], login_stats)

    root.mainloop()

if __name__ == "__main__":
    main()
