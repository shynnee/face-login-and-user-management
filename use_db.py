import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import io
import os


# Hàm để đọc thông tin người dùng đã đăng nhập từ file
def load_logged_in_user():
    if os.path.exists('logged_in_user.txt'):
        with open('logged_in_user.txt', 'r') as f:
            data = f.read().strip().split(',')
            if len(data) == 2:
                return data[0], data[1]
    return None, None


# Lấy thông tin người dùng đã đăng nhập
username, role = load_logged_in_user()


# Hàm kết nối cơ sở dữ liệu và truy vấn SQL
def execute_query(query, params=(), fetch_one=False):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute(query, params)
    results = c.fetchone() if fetch_one else c.fetchall()
    conn.commit()
    conn.close()
    return results


def fetch_blob_image(image_blob, size=(100, 100)):
    image = Image.open(io.BytesIO(image_blob))
    image = image.resize(size, Image.ANTIALIAS)
    return ImageTk.PhotoImage(image)


# Hàm hiển thị kết quả trong cửa sổ mới với tên cột thích hợp
def display_results(title, columns, results, has_image=False):
    def on_image_click(image_blob):
        image = Image.open(io.BytesIO(image_blob))
        image.show()

    win = tk.Toplevel()
    win.title(title)
    tree = ttk.Treeview(win, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=150, anchor='center')

    for row in results:
        tree.insert("", tk.END, values=row)

    if has_image:
        tree.bind("<Double-1>", lambda event: on_image_click(tree.item(tree.selection())['values'][1]))

    tree.pack(expand=True, fill='both')
    win.geometry("800x600")


# Các chức năng dành cho admin
def add_user():
    full_name = simpledialog.askstring("Input", "Enter full name:")
    username = simpledialog.askstring("Input", "Enter username:")
    password = simpledialog.askstring("Input", "Enter password:")
    email = simpledialog.askstring("Input", "Enter email:")
    address = simpledialog.askstring("Input", "Enter address:")
    if full_name and username and password and email and address:
        execute_query("INSERT INTO users (full_name, username, password, role) VALUES (?, ?, ?, ?)",
                      (full_name, username, password, 'user'))
        execute_query("INSERT INTO user_details (username, email, address, face_image) VALUES (?, ?, ?, ?)",
                      (username, email, address, b''))  # Assuming face_image is handled elsewhere
        execute_query("INSERT INTO registration_time (username) VALUES (?)", (username,))
        execute_query("INSERT INTO login_stats (username) VALUES (?)", (username,))
        messagebox.showinfo("Success", "User added successfully.")
    else:
        messagebox.showerror("Error", "All fields are required.")


def update_user():
    username = simpledialog.askstring("Input", "Enter username to update:")
    field = simpledialog.askstring("Input", "Enter field to update (full_name, password, email, address):")
    new_value = simpledialog.askstring("Input", "Enter new value:")
    if username and field and new_value:
        if field in ['full_name', 'password']:
            execute_query(f"UPDATE users SET {field} = ? WHERE username = ?", (new_value, username))
        elif field in ['email', 'address']:
            execute_query(f"UPDATE user_details SET {field} = ? WHERE username = ?", (new_value, username))
        messagebox.showinfo("Success", "User information updated successfully.")
    else:
        messagebox.showerror("Error", "All fields are required.")


def delete_user():
    username = simpledialog.askstring("Input", "Enter username to delete:")
    if username:
        execute_query("DELETE FROM users WHERE username = ?", (username,))
        execute_query("DELETE FROM user_details WHERE username = ?", (username,))
        execute_query("DELETE FROM registration_time WHERE username = ?", (username,))
        execute_query("DELETE FROM login_stats WHERE username = ?", (username,))
        messagebox.showinfo("Success", "User deleted successfully.")
    else:
        messagebox.showerror("Error", "Username is required.")


def show_all_users():
    query = """
    SELECT u.full_name, u.username,u.password,  d.email, d.address, r.registration_time, l.login_count, l.last_login_time
    FROM users u
    JOIN user_details d ON u.username = d.username
    JOIN registration_time r ON u.username = r.username
    JOIN login_stats l ON u.username = l.username
    """
    results = execute_query(query)
    columns = (
    "full_name", "username", "password", "email", "address", "registration_time", "login_count", "last_login_time")
    display_results("All Users", columns, results)


def show_statistics():
    # Tổng số người dùng
    total_users_query = "SELECT COUNT(*) FROM users"
    total_users = execute_query(total_users_query, fetch_one=True)[0]

    # Tổng số lượt đăng nhập
    total_logins_query = "SELECT SUM(login_count) FROM login_stats"
    total_logins = execute_query(total_logins_query, fetch_one=True)[0]

    # Số lượng đăng nhập trung bình mỗi người dùng
    avg_logins_per_user = total_logins / total_users if total_users > 0 else 0

    # Người dùng có nhiều lượt đăng nhập nhất
    max_logins_user_query = """
    SELECT u.full_name, u.username, l.login_count
    FROM users u
    JOIN login_stats l ON u.username = l.username
    ORDER BY l.login_count DESC
    LIMIT 1
    """
    max_logins_user = execute_query(max_logins_user_query, fetch_one=True)

    # Người dùng có ít lượt đăng nhập nhất
    min_logins_user_query = """
    SELECT u.full_name, u.username, l.login_count
    FROM users u
    JOIN login_stats l ON u.username = l.username
    ORDER BY l.login_count ASC
    LIMIT 1
    """
    min_logins_user = execute_query(min_logins_user_query, fetch_one=True)

    stats = f"""
    Total Users: {total_users}
    Total Logins: {total_logins}
    Average Logins per User: {avg_logins_per_user:.2f}

    User with Most Logins: 
    - Full Name: {max_logins_user[0]}
    - Username: {max_logins_user[1]}
    - Login Count: {max_logins_user[2]}

    User with Least Logins: 
    - Full Name: {min_logins_user[0]}
    - Username: {min_logins_user[1]}
    - Login Count: {min_logins_user[2]}
    """

    messagebox.showinfo("Statistics", stats)


def custom_sql_query():
    query = simpledialog.askstring("Input", "Enter SQL query:")
    if query:
        results = execute_query(query)
        columns = [desc[0] for desc in execute_query(f"PRAGMA table_info({query.split(' ')[3]})")]
        display_results("Custom SQL Query Results", columns, results)


# Các chức năng dành cho người dùng
def search_user(criteria):
    value = simpledialog.askstring("Input", f"Enter {criteria}:")
    if value:
        column = 'u.' + criteria if criteria in ['username', 'full_name'] else 'd.' + criteria
        query = f"""
            SELECT u.full_name, d.face_image, d.email, d.address, l.last_login_time
            FROM users u
            JOIN user_details d ON u.username = d.username
            JOIN login_stats l ON u.username = l.username
            WHERE {column} LIKE ?
        """
        results = execute_query(query, ('%' + value + '%',))
        columns = ("full_name", "face_image", "email", "address", "last_login_time")
        display_results("Search Results", columns, results, has_image=True)
    else:
        messagebox.showerror("Error", f"{criteria.capitalize()} is required.")




def update_user_info():
    def save_changes():
        new_full_name = full_name_entry.get()
        new_email = email_entry.get()
        new_address = address_entry.get()
        if new_full_name:
            execute_query("UPDATE users SET full_name = ? WHERE username = ?", (new_full_name, username))
        if new_email:
            execute_query("UPDATE user_details SET email = ? WHERE username = ?", (new_email, username))
        if new_address:
            execute_query("UPDATE user_details SET address = ? WHERE username = ?", (new_address, username))
        messagebox.showinfo("Success", "User information updated successfully.")
        update_win.destroy()

    def change_face_image():
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'rb') as file:
                blob_data = file.read()
                execute_query("UPDATE user_details SET face_image = ? WHERE username = ?", (blob_data, username))
                face_image = fetch_blob_image(blob_data)
                face_image_label.config(image=face_image)
                face_image_label.image = face_image

    update_win = tk.Toplevel()
    update_win.title("Update User Info")

    user_details = execute_query(
        "SELECT u.full_name, d.email, d.address, d.face_image FROM users u JOIN user_details d ON u.username = d.username WHERE u.username = ?",
        (username,), fetch_one=True)
    current_full_name, current_email, current_address, current_face_image = user_details

    tk.Label(update_win, text="Full Name:").grid(row=0, column=0, padx=10, pady=10)
    full_name_entry = tk.Entry(update_win)
    full_name_entry.insert(0, current_full_name)
    full_name_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(update_win, text="Email:").grid(row=1, column=0, padx=10, pady=10)
    email_entry = tk.Entry(update_win)
    email_entry.insert(0, current_email)
    email_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(update_win, text="Address:").grid(row=2, column=0, padx=10, pady=10)
    address_entry = tk.Entry(update_win)
    address_entry.insert(0, current_address)
    address_entry.grid(row=2, column=1, padx=10, pady=10)

    tk.Label(update_win, text="Face Image:").grid(row=3, column=0, padx=10, pady=10)
    face_image_label = tk.Label(update_win)
    face_image_label.grid(row=3, column=1, padx=10, pady=10)
    if current_face_image:
        face_image = fetch_blob_image(current_face_image)
        face_image_label.config(image=face_image)
        face_image_label.image = face_image
    tk.Button(update_win, text="Change Image", command=change_face_image).grid(row=3, column=2, padx=10, pady=10)

    tk.Button(update_win, text="Save Changes", command=save_changes).grid(row=4, column=0, columnspan=3, pady=20)


def change_password():
    def save_new_password():
        current_password = current_password_entry.get()
        new_password = new_password_entry.get()
        confirm_password = confirm_password_entry.get()

        if new_password != confirm_password:
            messagebox.showerror("Error", "New password and confirm password do not match.")
            return

        user = execute_query("SELECT password FROM users WHERE username = ?", (username,), fetch_one=True)
        if user and user[0] == current_password:
            execute_query("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
            messagebox.showinfo("Success", "Password updated successfully.")
            password_win.destroy()
        else:
            messagebox.showerror("Error", "Current password is incorrect.")

    password_win = tk.Toplevel()
    password_win.title("Change Password")

    tk.Label(password_win, text="Current Password:").grid(row=0, column=0, padx=10, pady=10)
    current_password_entry = tk.Entry(password_win, show="*")
    current_password_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(password_win, text="New Password:").grid(row=1, column=0, padx=10, pady=10)
    new_password_entry = tk.Entry(password_win, show="*")
    new_password_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(password_win, text="Confirm Password:").grid(row=2, column=0, padx=10, pady=10)
    confirm_password_entry = tk.Entry(password_win, show="*")
    confirm_password_entry.grid(row=2, column=1, padx=10, pady=10)

    tk.Button(password_win, text="Save", command=save_new_password).grid(row=3, column=0, columnspan=2, pady=20)


def show_top_users():
    query = """
    SELECT u.full_name, u.username, l.login_count
    FROM users u
    JOIN login_stats l ON u.username = l.username
    ORDER BY l.login_count DESC
    """
    results = execute_query(query)
    columns = ("full_name", "username", "login_count")
    display_results("Top Users", columns, results)


def filter_users(criteria, value):
    query = f"""
    SELECT u.full_name, u.username, d.email, d.address, r.registration_time, l.login_count, l.last_login_time
    FROM users u
    JOIN user_details d ON u.username = d.username
    JOIN registration_time r ON u.username = r.username
    JOIN login_stats l ON u.username = l.username
    WHERE {criteria} = ?
    """
    results = execute_query(query, (value,))
    columns = ("full_name", "username", "email", "address", "registration_time", "login_count", "last_login_time")
    display_results(f"Filtered Users by {criteria.capitalize()}", columns, results)


# Chuyển đổi giữa các khung
def raise_frame(frame):
    frame.tkraise()


root = tk.Tk()
root.geometry("1000x700")
root.configure(bg='white')

user_frame = tk.Frame(root)
admin_frame = tk.Frame(root)
for frame in (user_frame, admin_frame):
    frame.grid(row=0, column=0, sticky='news')
    frame.configure(bg='white')

# Thiết lập giao diện cho người dùng
if role == 'user':
    tk.Label(user_frame, text=f'Welcome {username}', font=('Helvetica', 35), bg='white').pack(pady=20)
    tk.Button(user_frame, text="Search by Name", command=lambda: search_user('full_name'), font=('Helvetica', 20),
              bg='#b0c4de').pack(pady=10)
    tk.Button(user_frame, text="Search by Email", command=lambda: search_user('email'), font=('Helvetica', 20),
              bg='#b0c4de').pack(pady=10)
    tk.Button(user_frame, text="Search by Address", command=lambda: search_user('address'), font=('Helvetica', 20),
              bg='#b0c4de').pack(pady=10)
    tk.Button(user_frame, text="Search by Username", command=lambda: search_user('username'), font=('Helvetica', 20),
              bg='#b0c4de').pack(pady=10)
    tk.Button(user_frame, text="Show Top Users", command=show_top_users, font=('Helvetica', 20), bg='#b0c4de').pack(
        pady=10)
    tk.Button(user_frame, text="Update My Info", command=update_user_info, font=('Helvetica', 20), bg='#b0c4de').pack(
        pady=10)
    tk.Button(user_frame, text="Change Password", command=change_password, font=('Helvetica', 20), bg='#b0c4de').pack(
        pady=10)
else:
    tk.Label(admin_frame, text=f'Welcome Admin {username}', font=('Helvetica', 35), bg='white').pack(pady=20)
    tk.Button(admin_frame, text="Add User", command=add_user, font=('Helvetica', 20), bg='#ffcccb').pack(pady=10)
    tk.Button(admin_frame, text="Update User", command=update_user, font=('Helvetica', 20), bg='#ffcccb').pack(pady=10)
    tk.Button(admin_frame, text="Delete User", command=delete_user, font=('Helvetica', 20), bg='#ffcccb').pack(pady=10)
    tk.Button(admin_frame, text="Show All Users", command=show_all_users, font=('Helvetica', 20), bg='#ffcccb').pack(
        pady=10)
    tk.Button(admin_frame, text="Show Statistics", command=show_statistics, font=('Helvetica', 20), bg='#ffcccb').pack(
        pady=10)
    tk.Button(admin_frame, text="Custom SQL Query", command=custom_sql_query, font=('Helvetica', 20),
              bg='#ffcccb').pack(pady=10)
    tk.Button(admin_frame, text="Filter Users by Login Count > 5", command=lambda: filter_users('login_count', 5),
              font=('Helvetica', 20), bg='#ffcccb').pack(pady=10)

# Chuyển đến khung phù hợp dựa trên vai trò người dùng
if role == 'user':
    raise_frame(user_frame)
else:
    raise_frame(admin_frame)

root.mainloop()
