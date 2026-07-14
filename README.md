 Career Compass AI

An AI-powered Career Guidance Web Application that helps students discover suitable career paths based on their education, skills, interests, and career goals. The application uses Google's Gemini AI to generate personalized career recommendations and provides downloadable PDF reports.

---

 Project Overview

Career Compass AI is a full-stack Flask web application designed to assist students in making informed career decisions.

Users can:

- Create an account
- Log in securely
- Complete their academic profile
- Receive personalized AI-generated career guidance
- View recommendation history
- Download recommendations as PDF
- Manage their previous recommendations

The project combines Artificial Intelligence, Flask, MySQL, and modern web technologies to create an interactive career advisory platform.

---

 Features

 User Authentication

- User Registration
- Secure Login
- Logout
- Password Hashing using Flask-Bcrypt
- Session Management

---
 User Profile Management

Users can store:

- Education Level
- Stream / Branch
- Skills
- Interests
- Career Goal

Profile information can be updated anytime.

---

 AI Career Recommendation

Powered by **Google Gemini AI**

The AI analyzes the student's profile and generates:

- 3 Personalized Career Paths
- Required Skills
- Recommended Courses
- Learning Roadmap
- Next Career Steps
- Personalized Motivational Message

---

 Recommendation History

Users can:

- View all previously generated recommendations
- Open any recommendation
- Access recommendation details anytime

---

 📄 PDF Download

Users can download their AI recommendation as a professionally formatted PDF report.

---

 🗑 Delete Recommendation

Users can permanently remove old recommendations from their account.

---

⏱ Rate Limiting

To prevent excessive API usage,

- Users can generate one recommendation every **3 hours**.

---

⚠ Error Handling

Custom pages included for:

- 404 Page Not Found
- 500 Internal Server Error

---

 Technology Stack

Frontend

- HTML5
- CSS3
- Jinja2 Templates

 Backend

- Python
- Flask

Database

- MySQL

 AI

- Google Gemini API

Authentication

- Flask-Bcrypt

PDF Generation

- xhtml2pdf

Environment Variables

- python-dotenv

---

 Project Structure

```
CareerCampusAI/
│
├── static/
│   └── css/
│
├── templates/
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── recommendation.html
│   ├── history.html
│   ├── pdf_template.html
│   ├── 404.html
│   └── 500.html
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env (Not uploaded to GitHub)
```

---

# ⚙ Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/CareerCampusAI.git
```

---

## 2. Move into Project Folder

```bash
cd CareerCampusAI
```

---

## 3. Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

```bash
venv\Scripts\activate
```

---

## 4. Install Required Packages

```bash
pip install -r requirements.txt
```

---

## 5. Create .env File

Create a file named:

```
.env
```

Add:

```env
SECRET_KEY=your_secret_key

GEMINI_API_KEY=your_gemini_api_key

DB_PASSWORD=your_mysql_password
```

---

## 6. Configure MySQL Database

Create database:

```sql
career_compass_db
```

Create required tables before running the application.

---

## 7. Run the Application

```bash
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

# 📋 Application Workflow

1. Register a new account
2. Login securely
3. Complete your profile
4. Generate AI Career Recommendation
5. View recommendation
6. Download PDF
7. View recommendation history
8. Delete recommendations if needed

---

 Security Features

- Password Hashing
- Environment Variables
- Session Authentication
- Secure Login
- Rate Limiting
- Protected Routes

---

Screenshots

You can add screenshots of:

- Landing Page
- Login Page
- Register Page
- Dashboard
- Profile Page
- AI Recommendation
- Recommendation History
- PDF Download

Example:

```
screenshots/
    landing.png
    dashboard.png
    recommendation.png
```

---

Future Improvements

- Resume Analyzer
- Career Roadmap Generator
- Skill Gap Analysis
- Job Recommendation
- College Recommendation
- Email Verification
- Admin Dashboard
- Dark Mode
- Mobile Responsive UI
- Multi-language Support

---

 Python Packages Used

- Flask
- Flask-Bcrypt
- mysql-connector-python
- google-generativeai
- python-dotenv
- xhtml2pdf

---

 Author

**Harshavarthini M**

Information Technology Student

Career Compass AI Developer

---

License

This project is developed for educational and learning purposes.

Feel free to use, modify, and improve it for personal or academic use.

---

Support

If you found this project useful,

please consider giving it a on GitHub.

It motivates further development and improvements.
 