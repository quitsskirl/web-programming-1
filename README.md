# Mental Health Support Platform

A web application designed to connect students with mental health professionals and counselors.

## Features

- **User Authentication**: Separate login/registration for students and professionals
- **JWT Token Security**: Secure authentication using JSON Web Tokens
- **Password Hashing**: Passwords stored securely using scrypt algorithm with salt
- **Role-Based Access**: Different home pages for students and professionals
- **Counselor Services**: Browse and connect with mental health professionals
- **User Settings**: Manage account settings and profile
- **Responsive Design**: Beautiful nature-themed UI with animated floating leaves

## Tech Stack

- **Backend**: Python Flask
- **Database**: MongoDB Atlas
- **Authentication**: JWT (PyJWT)
- **Password Security**: Werkzeug (scrypt + salt)
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with nature theme

## Project Structure

```
web-programming-1/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── routs/                 # Flask Blueprints (routes)
│   ├── __init__.py
│   ├── first_page.py      # Landing page
│   ├── home.py            # Student home page
│   ├── HPprofessor.py     # Professor home page
│   ├── login_student.py   # Student login
│   ├── login_professional.py  # Professional login
│   ├── register_student.py    # Student registration
│   ├── register_professional.py  # Professional registration
│   ├── services.py        # Counselor services
│   ├── settings.py        # User settings
│   └── more_info.py       # Information page
├── templates/             # HTML templates
│   ├── FirstPage.html
│   ├── HomePage.html
│   ├── HPprofessor.html
│   ├── loginST.html
│   ├── loginPF.html
│   ├── registerST.html
│   ├── registrationPF.html
│   ├── Services.html
│   ├── Settings.html
│   └── MoreInfo.html
└── static/                # CSS, JS, and assets
    ├── loginST.css
    ├── loginPF.css
    ├── registerST.css
    ├── registrationPF.css
    ├── FirstPage1.css
    ├── HomePage1.css
    ├── HPprofessor1.css
    ├── Services1.css
    ├── Settings1.css
    └── MoreInfo1.css
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/quitsskirl/web-programming-1.git
cd web-programming-1
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Create Environment File

Create a `.env` file in the project root with:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
JWT_SECRET_KEY=your-secret-key-here
```

Replace with your actual MongoDB Atlas connection string and a secure secret key.

### 6. MongoDB Atlas Setup

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster
3. Add your IP address to the Network Access whitelist
4. Create a database user
5. Get your connection string and add it to `.env`

### 7. Run the Application

```bash
python app.py
```

The application will start at `http://127.0.0.1:5000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/home` | GET | Student home page |
| `/home-professor` | GET | Professor home page |
| `/login-student` | GET/POST | Student login |
| `/login-professional` | GET/POST | Professional login |
| `/register-student` | GET | Student registration form |
| `/register-professional` | GET | Professional registration form |
| `/services` | GET | Counselor services page |
| `/settings` | GET | User settings page |
| `/more-info` | GET | Information page |
| `/api/login/student` | POST | Student login API |
| `/api/login/professional` | POST | Professional login API |
| `/api/register/professional` | POST | Professional registration API |
| `/api/verify-token` | GET | Verify JWT token |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | MongoDB Atlas connection string |
| `JWT_SECRET_KEY` | Secret key for JWT token signing |

## Security Features

- **Password Hashing**: All passwords are hashed using scrypt with a 16-byte random salt
- **JWT Authentication**: Stateless authentication with 24-hour token expiration
- **HTTP-Only Cookies**: Tokens stored in HTTP-only cookies to prevent XSS attacks
- **TLS Encryption**: Secure connection to MongoDB Atlas

## Authors

- Mental Health Support Team

## License

This project is for educational purposes.

