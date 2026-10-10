# FinZave 🚀

![FinZave Banner]

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](#)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## About FinZave

**FinZave** is a comprehensive, open-source personal finance management application. It empowers users to meticulously track income and expenses, analyze long-term spending habits, strategize financial goals, and make superior, data-driven financial decisions.

Built with modern web technologies, FinZave bridges the gap between complex financial planning and intuitive user experiences.

---

## 🌟 Features

FinZave includes a rich suite of tools designed for complete financial visibility:

- 💰 **Expense Tracking:** Log, categorize, and monitor daily spending.
- 💵 **Income Management:** Track variable and fixed income streams.
- 📊 **Financial Dashboard:** A high-level, real-time overview of your financial health.
- 📈 **Spending Analysis:** Deep-dive charts and algorithmic spending insights.
- 🎯 **Goal Tracking:** Set savings targets and track your progress automatically.
- 🏦 **SIP Planning:** Calculate Systematic Investment Plan (SIP) returns.
- 🚗 **EMI Planning:** Calculate Equated Monthly Installments for loans.
- 📄 **PDF Reports:** Generate and export beautiful, professional financial statements.
- 🛠️ **Admin Dashboard:** Secure administration panel for system management.

---

## 🏗️ System Architecture

FinZave utilizes a robust, decoupled MVC-style architecture.

**Frontend:**
- HTML5 (Jinja2 Templates)
- Tailwind CSS (Utility-first styling)
- Vanilla JavaScript (Dynamic UI and asynchronous API requests)

**Backend:**
- Python (Core logic)
- Flask (Web framework)
- SQLAlchemy (ORM)
- Flask-JWT-Extended (Stateless authentication)

**Database:**
- SQLite (Development) / PostgreSQL (Production)

### Application Data Flow

```text
User 
  ↓ (HTTP Requests)
Frontend (Jinja Templates / JS)
  ↓ (JSON / Form Data)
Flask Routes (Controllers & JWT Auth)
  ↓ (Data Validation)
Business Logic (utils/finance.py)
  ↓ (SQLAlchemy ORM)
Database
```

---

## 📂 Project Structure

```text
FinZave/
├── analysis/         # Algorithmic health scoring and analysis engines
├── migrations/       # Alembic database schema migrations
├── models/           # SQLAlchemy database tables (User, Expense, Income, etc.)
├── planning/         # Financial calculators (SIP, EMI)
├── routes/           # Flask Blueprints (API endpoints and View controllers)
├── static/           # CSS stylesheets, Javascript modules, and static images
├── templates/        # Jinja2 HTML rendering templates
├── tests/            # Comprehensive Pytest suite ensuring 100% stability
├── utils/            # Core financial engine, caching, and background helpers
├── .env.example      # Template for required environment variables
├── app.py            # Flask application factory and entry point
├── config.py         # Application configuration loader
└── extensions.py     # Global extension instantiations (DB, JWT, Limiter)
```

---

## 🚀 Installation Guide

Follow these steps to run FinZave locally.

### 1. Clone the Project
```bash
git clone https://github.com/yourusername/finzave.git
cd finzave
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
Create a `.env` file in the root directory (you can copy `.env.example` if available) and add the following:
```env
FLASK_ENV=development
FLASK_APP=app.py
DATABASE_URL=sqlite:///finzave.db
SECRET_KEY=your_secure_random_flask_key_here
JWT_SECRET_KEY=your_secure_random_jwt_key_here
```

### 5. Initialize Database & Run
```bash
flask db upgrade
flask run
```
Access the application at `http://127.0.0.1:5000/`.

---

## 🔐 Security Features

FinZave is built with modern web security standards:
- **Password Hashing:** Bcrypt encryption secures all user passwords.
- **JWT Authentication:** Secure, stateless sessions using HTTP-Only cookies.
- **CSRF Protection:** Hardened API endpoints prevent cross-site request forgery.
- **Environment Secrets:** Sensitive credentials are strictly isolated from the codebase.
- **User Data Isolation:** SQL queries are strictly scoped to the authenticated user's ID.

---

## 🧪 Testing

FinZave includes a robust, isolated test suite using `pytest`.

```bash
pytest tests/ -v
```

**Current Coverage Includes:**
- Authentication (Login/Register/JWT)
- Financial Engine Calculations
- Transactions (Income/Expense/Limits)
- Goal Tracking & SIP/EMI Planners
- Report Generation

---

## 📸 Screenshots

*(Placeholder for future screenshots)*

### Dashboard
![Dashboard](https://via.placeholder.com/800x400.png?text=Dashboard+Preview)

### Financial Analysis
![Analysis](https://via.placeholder.com/800x400.png?text=Analysis+Preview)

---

## 🔮 Future Improvements

- **Email Verification:** Mandate email confirmation upon registration.
- **Background CSV Processing:** Implement Celery/Redis to parse massive bank statement uploads asynchronously.
- **Advanced Analytics:** AI-driven categorized budget recommendations.

---

## 🤝 Contribution

Contributions are welcome! Please fork the repository, create a feature branch, and submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.