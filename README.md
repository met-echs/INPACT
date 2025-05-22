
# 🤖 AI Interview System

An AI-powered Interview Management System built using Django (Python), HTML, CSS, JavaScript, PostgreSQL, Groq API for AI interviews, and email integration.

---

## 🌟 Features

- AI interview assistant using Groq API
- Resume evaluation and scoring
- Email notifications to candidates
- Admin panel for managing interviews
- PostgreSQL database integration
- Responsive UI with HTML, CSS, and JavaScript

---

## 📁 Project Structure

```
ai-interview/
│
├── backend/             # Django backend
│   ├── manage.py
│   ├── settings.py
│   ├── .env.sample
|   ├── requirements.txt      # Sample environment variables (copy this to .env)
│   └── ...
│
├── frontend/            # Static frontend assets (HTML, CSS, JS)    # Backend Python dependencies
└── README.md            # This file
```

---

## 🚀 Getting Started

### 1. 📦 Clone the Repository

```bash
git clone https://github.com/met-echs/AI-INTERVIEW-WEB.git
cd AI-INTERVIEW-WEB
```

---

### 2. 🐍 Create and Activate a Virtual Environment

#### 🔷 Windows (CMD or PowerShell)

```bash
python -m venv venv
venv\Scripts\activate
```

#### 🍎 macOS / 🐧 Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. 📥 Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

### 4. ⚙️ Set Environment Variables

- Inside the `backend/` folder, copy the sample env file:

```bash
cp .env.sample .env
```

- Edit `.env` and fill in your actual values:

```env
# Django secret key
SECRET_KEY=your_django_secret_key_here

# Database configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_database_name
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Email configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password_or_app_password

# External API keys
GROQ_API_KEY=your_groq_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

> 🔐 **Important:** Never commit your real `.env` file to GitHub.

---

### 5. 🔧 Apply Migrations

```bash
python manage.py migrate
```

---

### 6. ▶️ Start the Django Development Server

```bash
python manage.py runserver
```

- Server URL: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 👩‍💻 Creating Admin User from Django Shell

If you use a custom `Admin` model like this:

```python
class Admin(models.Model):
    username = models.EmailField(unique=True, verbose_name="Email Address")
    password = models.CharField(max_length=255, verbose_name="Password")
```

### Create an admin user via shell:

```bash
python manage.py shell
```

```python
from your_app_name.models import Admin

admin = Admin(username='admin@example.com', password='admin123')
admin.save()
print("Admin user created:", admin.username)
```



## 🧪 Optional

### Django Admin

- To access: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- Create superuser:

```bash
python manage.py createsuperuser
```

---

## 📧 Contact

For support, contact [amilmether37@gmail.com](mailto:amilmether37@gmail.com)

---

## 🛡 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more info.
