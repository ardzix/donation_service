
# 🧭 Campaign Donation Management API

A Django-based microservice for managing user-generated fundraising campaigns, donation tracking, fund allocation transparency, and withdrawal monitoring — complete with RESTful APIs and Swagger documentation.

---

## 📌 Features

- 👤 User-generated campaign creation and management
- 🔗 Multiple placements per campaign (e.g., billboards, web banners)
- 💸 Transparent donation tracking via QR or link
- 📊 Automatic fund allocation with FIFO logic
- 🧾 Expense tracking per campaign
- ✅ Admin-controlled fund withdrawal system
- 🔐 Authentication via existing SSO
- 📑 Full Swagger & ReDoc API documentation via `drf-yasg`
- ⚙️ Designed for microservices using Apache Pulsar for event handling (future-ready)

---

## 🚀 Tech Stack

| Layer        | Technology                 |
|-------------|----------------------------|
| Backend      | Django, Django REST Framework |
| Auth         | Existing SSO via JWT or session |
| Messaging    | Apache Pulsar (planned)    |
| Docs         | drf-yasg (Swagger + ReDoc) |
| Database     | PostgreSQL                 |
| Caching      | Redis (optional)           |
| Permissions  | Role-based + ownership checks |

---

## 📂 Project Structure (Core)

```bash
.
├── campaigns/
│   ├── models.py          # All DB models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # Campaign + related views
│   ├── urls.py            # API routes
│   ├── admin.py           # Admin panel setup
│   └── templates/
│       └── homepage.html  # Modern landing page
├── donation_project/
│   └── urls.py            # Global URLs including Swagger
└── manage.py
```

---

## ⚙️ Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/campaign-donation-api.git
cd campaign-donation-api
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` and Configure Database
Update your DB credentials inside `.env` or directly in `settings.py`.

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Run the Server
```bash
python manage.py runserver
```

---

## 🔐 Authentication

This service assumes authentication is handled via your existing SSO layer. All endpoints are protected via:

```python
permission_classes = [IsAuthenticated]
```

---

## 📚 API Documentation

| Type   | URL |
|--------|-----|
| Swagger | [`/swagger/`](http://localhost:8000/swagger/) |
| ReDoc   | [`/redoc/`](http://localhost:8000/redoc/) |
| JSON    | [`/swagger.json`](http://localhost:8000/swagger.json) |

---

## 🛠️ Endpoints Overview

| Resource       | Base URL                  | Access                   |
|----------------|---------------------------|--------------------------|
| Campaigns      | `/api/campaigns/`         | UGC - only owner can manage |
| Placements     | `/api/placements/?campaign=<uuid>` | Requires campaign UUID |
| Donations      | `/api/donations/?campaign=<uuid>`  | Requires campaign UUID |
| Expenses       | `/api/expenses/?campaign=<uuid>`   | Requires campaign UUID |
| Allocations    | `/api/allocations/?campaign=<uuid>`| Read-only + UUID filter |
| Withdrawals    | `/api/withdrawals/?campaign=<uuid>`| Requires campaign UUID |

All data access is **scoped per user** except `GET /campaigns/<external_id>/`, which is public.

---

## 🌱 Contribution Guide

### 🧪 Run Tests
```bash
# coming soon - pytest setup
```

### 🔧 Format Code
```bash
black .
```

### 📝 Want to contribute?

1. Fork the project
2. Create your feature branch: `git checkout -b feature/my-awesome-thing`
3. Commit your changes: `git commit -m 'Add some awesome thing'`
4. Push to the branch: `git push origin feature/my-awesome-thing`
5. Open a pull request 🚀

---

## 📞 Contact

Maintained by [@yourname](https://github.com/yourname)  
Feel free to open issues or suggest improvements.

---

## 📄 License

This project is licensed under the [BSD License](https://opensource.org/licenses/BSD-3-Clause).