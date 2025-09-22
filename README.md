# Coffee framework

```
Author: thinhnguyen@wearetopgroup.com
```

## Yêu cầu hệ thống

- Python (>= 3.12)
- pip (công cụ quản lý package của Python)
- Git

## Cấu trúc thư mục

```
coffee/
├── venv/                 # Môi trường ảo
├── requirements.txt      # File chứa danh sách package
├── setup/setup_linux.sh  # Script cài đặt cho Linux/Mac
├── setup/setup_win.bat   # Script cài đặt cho Windows
└── README.md             # File hướng dẫn này
```

## Cách setup dự án

### 1. Clone dự án (nếu có)

```bash
git clone git@github.com:digitopvn/django.git
cd django
```

### 2. Cài đặt tự động

#### Windows

1. Chạy file `setup.bat` bằng cách:
   - Double-click vào file `setup.bat`, hoặc
   - Mở Command Prompt và chạy:
     ```cmd
     setup.bat
     ```

#### Linux/Mac

1. Cấp quyền thực thi cho file setup:

   ```bash
   chmod +x setup.sh
   ```

2. Chạy file setup:
   ```bash
   ./setup.sh
   ```

### 3. Cài đặt thủ công

Nếu không muốn sử dụng script tự động, bạn có thể thực hiện các bước sau:

1. Tạo môi trường ảo:

   ```bash
   # Windows
   python -m venv venv

   # Linux/Mac
   python3 -m venv venv
   ```

2. Kích hoạt môi trường ảo:

   ```bash
   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. Cài đặt các package:
   ```bash
   pip install -r requirements.txt
   ```

## Kiểm tra cài đặt

1. Kiểm tra Django đã được cài đặt:

   ```bash
   python -m django --version
   ```

2. Tạo project mới (nếu cần):
   ```bash
   django-admin startproject your_project_name
   ```

## Khởi chạy dự án

1. Di chuyển vào thư mục project:

   ```bash
   cd django
   ```

2. Chạy migrations:

   ```bash
   python manage.py migrate
   ```

3. Khởi động server:

   ```bash
   python manage.py runserver
   ```

4. Truy cập website tại: http://127.0.0.1:8000/

## Các package được cài đặt

- django==5.0.1
- djangorestframework==3.14.0
- python-dotenv==1.0.0
- pillow==10.2.0
- psycopg2-binary==2.9.9
- django-cors-headers==4.3.1

## Xử lý sự cố

### 1. Lỗi không tìm thấy package

```bash
pip install -r requirements.txt --no-cache-dir
```

### 2. Lỗi môi trường ảo

Xóa thư mục venv và tạo lại:

```bash
# Windows
rmdir venv /s /q
python -m venv venv

# Linux/Mac
rm -rf venv
python3 -m venv venv
```

### 3. Lỗi port 8000 đã được sử dụng

Chạy server với port khác:

```bash
python manage.py runserver 8001
```

## Lưu ý quan trọng

1. Luôn kích hoạt môi trường ảo trước khi làm việc với project
2. Không commit thư mục venv lên git
3. Cập nhật requirements.txt khi thêm package mới:
   ```bash
   pip freeze > requirements.txt
   ```
4. Chạy pre-commit test
   ```
      pre-commit run --all-files
   ```

## Hỗ trợ

Nếu bạn gặp vấn đề trong quá trình cài đặt, vui lòng:

1. Kiểm tra phiên bản Python và pip
2. Đảm bảo đã kích hoạt môi trường ảo
3. Đọc thông báo lỗi và tìm giải pháp trong phần "Xử lý sự cố"
4. Tạo issue trên repository (nếu có) với mô tả chi tiết vấn đề

# Git Commit Guide

## Setup

1. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

2. Chạy script cài đặt hooks:

```bash
python install_hooks.py
```

## Quy tắc Commit

### Cách commit code:

Thay vì dùng `git commit -m "message"`, sử dụng:

```bash
python commit.py
```

### Format commit message:

```
<type>(<scope>): <message>

[optional body]

[optional BREAKING CHANGE]
```

### Các loại commit:

- ✨ feat: Tính năng mới
- 🐛 fix: Sửa lỗi
- 📚 docs: Thay đổi documentation
- 💎 style: Format code, sửa linting
- ♻️ refactor: Refactor code
- 🧪 test: Thêm/sửa test
- 🔧 chore: Công việc maintainance

### Scopes:

- api: API changes
- ui: UI changes
- auth: Authentication
- db: Database
- core: Core functionality
- test: Testing
- deps: Dependencies
- ci: CI/CD
- docs: Documentation

## Ví dụ:

```
feat(auth): add OAuth2 login support

- Added Google OAuth2 provider
- Implemented token refresh
- Added user profile sync

BREAKING CHANGE: Previous login tokens will be invalidated
```

## Lưu ý:

- Không thể commit trực tiếp mà không qua commit helper
- Mỗi commit phải có type và message rõ ràng
- Breaking changes phải được đánh dấu
- Scope là optional nhưng khuyến khích dùng
