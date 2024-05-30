import face_recognition
import cv2
import pickle
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sqlite3
import datetime
import sys

# Create the images directory if it doesn't exist
images_dir = 'images'
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

# Hàm để lưu thông tin người dùng vào cơ sở dữ liệu
def save_user_to_db(full_name, username, password, email, address, face_image_path, role='user'):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    # Lưu thông tin cơ bản vào bảng users
    c.execute("INSERT INTO users (full_name, username, password, role) VALUES (?, ?, ?, ?)",
              (full_name, username, password, role))

    # Đọc ảnh khuôn mặt và lưu vào bảng user_details
    with open(face_image_path, 'rb') as f:
        face_image = f.read()
    c.execute("INSERT INTO user_details (username, face_image, email, address) VALUES (?, ?, ?, ?)",
              (username, face_image, email, address))

    # Lưu thời gian đăng ký vào bảng registration_time
    c.execute("INSERT INTO registration_time (username) VALUES (?)", (username,))

    # Khởi tạo số lần đăng nhập và thời gian đăng nhập gần nhất
    c.execute("INSERT INTO login_stats (username, login_count, last_login_time) VALUES (?, 0, NULL)", (username,))

    conn.commit()
    conn.close()

# Hàm để cập nhật thông tin đăng nhập
def update_login_stats(username):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    # Cập nhật số lần đăng nhập và thời gian đăng nhập gần nhất
    c.execute("UPDATE login_stats SET login_count = login_count + 1, last_login_time = ? WHERE username = ?",
              (datetime.datetime.now(), username))

    conn.commit()
    conn.close()

class Dlib_Face_Unlock:
    def __init__(self):
        try:
            with open('labels.pickle', 'rb') as self.f:
                self.og_labels = pickle.load(self.f)
            print(self.og_labels)
        except FileNotFoundError:
            print("No label.pickle file detected, will create required pickle files")

        self.current_id = 0
        self.labels_ids = {}
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.image_dir = os.path.join(self.BASE_DIR, images_dir)
        for self.root, self.dirs, self.files in os.walk(self.image_dir):
            for self.file in self.files:
                if self.file.endswith('jpg'):  # Changed to 'jpg'
                    self.path = os.path.join(self.root, self.file)
                    self.label = os.path.basename(os.path.dirname(self.path)).replace(' ', '-').lower()
                    if self.label not in self.labels_ids:
                        self.labels_ids[self.label] = self.current_id
                        self.current_id += 1
                        self.id = self.labels_ids[self.label]

        print(self.labels_ids)
        self.og_labels = 0
        if self.labels_ids != self.og_labels:
            with open('labels.pickle', 'wb') as self.file:
                pickle.dump(self.labels_ids, self.file)

            self.known_faces = []
            for self.i in self.labels_ids:
                noOfImgs = len([filename for filename in os.listdir(os.path.join(images_dir, self.i))
                                if os.path.isfile(os.path.join(images_dir, self.i, filename)) and filename.endswith('jpg')])  # Changed to 'jpg'
                print(noOfImgs)
                for imgNo in range(1, (noOfImgs + 1)):
                    self.directory = os.path.join(self.image_dir, self.i, str(imgNo) + '.jpg')  # Changed to 'jpg'
                    self.img = face_recognition.load_image_file(self.directory)
                    self.img_encoding = face_recognition.face_encodings(self.img)[0]
                    self.known_faces.append([self.i, self.img_encoding])
            print(self.known_faces)
            print("No Of Imgs" + str(len(self.known_faces)))
            with open('KnownFace.pickle', 'wb') as self.known_faces_file:
                pickle.dump(self.known_faces, self.known_faces_file)
        else:
            with open('KnownFace.pickle', 'rb') as self.faces_file:
                self.known_faces = pickle.load(self.faces_file)
            print(self.known_faces)

    def ID(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.face_names = []
        while self.running:
            self.ret, self.frame = self.cap.read()
            self.small_frame = cv2.resize(self.frame, (0, 0), fx=0.5, fy=0.5)
            self.rgb_small_frame = self.small_frame[:, :, ::-1]
            if self.running:
                self.face_locations = face_recognition.face_locations(self.frame)
                self.face_encodings = face_recognition.face_encodings(self.frame, self.face_locations)
                self.face_names = []
                for self.face_encoding in self.face_encodings:
                    for self.face in self.known_faces:
                        self.matches = face_recognition.compare_faces([self.face[1]], self.face_encoding)
                        print(self.matches)
                        self.name = 'Unknown'
                        self.face_distances = face_recognition.face_distance([self.face[1]], self.face_encoding)
                        self.best_match = np.argmin(self.face_distances)
                        print(self.best_match)
                        print('This is the match in best match', self.matches[self.best_match])
                        if self.matches[self.best_match] == True:
                            self.running = False
                            self.face_names.append(self.face[0])
                            break
                        next
            print("The best match(es) is" + str(self.face_names))
            self.cap.release()
            cv2.destroyAllWindows()
            break
        return self.face_names


def login_user():
    dfu = Dlib_Face_Unlock()
    faceName = dfu.ID()
    if faceName == []:
        messagebox.showerror("Login Error", "No face detected. Please try again.")
    else:
        username = faceName[0]
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute("SELECT full_name, role FROM users WHERE username=?", (username,))
        result = c.fetchone()
        if result:
            loggedInUser.set(result[0])
            update_login_stats(username)
            with open('logged_in_user.txt', 'w') as f:
                f.write(f"{username},{result[1]}")
            sys.exit(0)
        else:
            messagebox.showerror("Login Error", "User not found. Please register.")

def login_user_info():
    username = username_var.get()
    password = password_var.get()
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT full_name, role FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    if username == "root" and password == "admin":
        loggedInUser.set("Admin")
        with open('logged_in_user.txt', 'w') as f:
            f.write("Shyn,admin")
        sys.exit(0)
    else:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute("SELECT full_name FROM users WHERE username=? AND password=?", (username, password))
        result = c.fetchone()
        if result:
            loggedInUser.set(result[0])
            update_login_stats(username)
            with open('logged_in_user.txt', 'w') as f:
                f.write(f"{username},user")
            sys.exit(0)
        else:
            messagebox.showerror("Login Error", "Invalid username or password.")

def register():
    full_name = name.get()
    username_value = username.get()
    password_value = password.get()
    email_value = email.get()
    address_value = address.get()

    # Create a subfolder for the username inside the images directory
    user_image_dir = os.path.join(images_dir, username_value)
    if not os.path.exists(user_image_dir):
        os.makedirs(user_image_dir)

    # Save the face image captured from the webcam
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        messagebox.showerror("Registration Error", "Failed to capture image. Please try again.")
        return

    # Determine the next image number
    existing_images = [f for f in os.listdir(user_image_dir) if os.path.isfile(os.path.join(user_image_dir, f))]
    image_number = len(existing_images) + 1
    face_image_path = os.path.join(user_image_dir, f"{image_number}.jpg")
    cv2.imwrite(face_image_path, frame)

    if full_name and username_value and password_value and email_value and address_value:
        save_user_to_db(full_name, username_value, password_value, email_value, address_value, face_image_path)
        messagebox.showinfo("Registration", "Registration successful!")
        raiseFrame(loginFrame)
    else:
        messagebox.showerror("Registration Error", "All fields are required.")


root = tk.Tk()
root.geometry("1000x700")
root.configure(bg='white')
loginFrame = tk.Frame(root)
regFrame = tk.Frame(root)
userMenuFrame = tk.Frame(root)
userLoginFrame = tk.Frame(root)

for frame in (loginFrame, regFrame, userMenuFrame, userLoginFrame):
    frame.grid(row=0, column=0, sticky='news')
    frame.configure(bg='white')

def raiseFrame(frame):
    frame.tkraise()

def regFrameRaiseFrame():
    raiseFrame(regFrame)

def userMenuFrameRaiseFrame():
    raiseFrame(userMenuFrame)

def userLoginFrameRaiseFrame():
    raiseFrame(userLoginFrame)

raiseFrame(loginFrame)

loggedInUser = tk.StringVar()

# Login Frame
tk.Label(loginFrame, text='Login or Register', font=('Helvetica', 35), bg='white').pack(pady=20)
tk.Button(loginFrame, text="Login", font=('Helvetica', 20), bg='#b0c4de', command=userLoginFrameRaiseFrame).pack(pady=10)
tk.Button(loginFrame, text="Register", font=('Helvetica', 20), bg='#b0c4de', command=regFrameRaiseFrame).pack(pady=10)

# Register Frame
tk.Label(regFrame, text='Register', font=('Helvetica', 35), bg='white').pack(pady=20)
tk.Label(regFrame, text='Name', font=('Helvetica', 20), bg='white').pack(pady=10)
name = tk.Entry(regFrame, font=('Helvetica', 20))
name.pack()
tk.Label(regFrame, text='Username', font=('Helvetica', 20), bg='white').pack(pady=10)
username = tk.Entry(regFrame, font=('Helvetica', 20))
username.pack()
tk.Label(regFrame, text='Password', font=('Helvetica', 20), bg='white').pack(pady=10)
password = tk.Entry(regFrame, font=('Helvetica', 20))
password.pack()
tk.Label(regFrame, text='Email', font=('Helvetica', 20), bg='white').pack(pady=10)
email = tk.Entry(regFrame, font=('Helvetica', 20))
email.pack()
tk.Label(regFrame, text='Address', font=('Helvetica', 20), bg='white').pack(pady=10)
address = tk.Entry(regFrame, font=('Helvetica', 20))
address.pack()
tk.Button(regFrame, text="Register", font=('Helvetica', 20), bg='#b0c4de', command=register).pack(pady=20)
tk.Button(regFrame, text="Back to Login", font=('Helvetica', 20), bg='#b0c4de', command=lambda: raiseFrame(loginFrame)).pack(pady=10)

# User Login Frame
tk.Label(userLoginFrame, text='User Login', font=('Helvetica', 35), bg='white').pack(pady=20)
tk.Label(userLoginFrame, text='Username', font=('Helvetica', 20), bg='white').pack(pady=10)
username_var = tk.StringVar()
username_entry = tk.Entry(userLoginFrame, textvariable=username_var, font=('Helvetica', 20))
username_entry.pack()
tk.Label(userLoginFrame, text='Password', font=('Helvetica', 20), bg='white').pack(pady=10)
password_var = tk.StringVar()
password_entry = tk.Entry(userLoginFrame, textvariable=password_var, font=('Helvetica', 20), show='*')
password_entry.pack()
tk.Button(userLoginFrame, text="Login with Face Recognition", font=('Helvetica', 20), bg='#b0c4de', command=login_user).pack(pady=10)
tk.Button(userLoginFrame, text="Login with Username & Password", font=('Helvetica', 20), bg='#b0c4de', command=login_user_info).pack(pady=10)
tk.Button(userLoginFrame, text="Back to Login", font=('Helvetica', 20), bg='#b0c4de', command=lambda: raiseFrame(loginFrame)).pack(pady=10)

root.mainloop()

