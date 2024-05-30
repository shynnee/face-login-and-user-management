import subprocess
import os
import sys

# Đường dẫn tới các file chính
main_script = 'main.py'
use_db_script = 'use_db.py'

# Hàm kiểm tra nếu người dùng đã đăng nhập
def is_logged_in():
    return os.path.exists('logged_in_user.txt')

# Chạy file main.py
subprocess.run([sys.executable, main_script])

# Kiểm tra nếu người dùng đã đăng nhập xong
if is_logged_in():
    # Chạy file use_db.py
    subprocess.run([sys.executable, use_db_script])
else:
    print("User login was not successful.")
