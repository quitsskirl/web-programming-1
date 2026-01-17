# Mental Health Support Platform

A web application designed to connect students with mental health professionals and counselors.

## Features

- **User Authentication**: Separate login/registration for students and professionals
- **JWT Token Security**: Secure authentication using JSON Web Tokens
- **Password Hashing**: Passwords stored securely using scrypt algorithm with salt
- **Password Management**: Change password with verification of current password
- **Password Visibility Toggle**: Show/hide password with eye icon in forms
- **Role-Based Access**: Different home pages for students and professionals
- **AI Support Classifier**: Classifies student messages to route to appropriate support (IDC, OPEN, COUNSEL)
- **Appointment Booking**: Students can book appointments with professionals
- **Resource Management**: Professionals can upload PDFs and videos for students
- **Event Image Slider**: Homepage slider with uploadable event images
- **Feedback System**: Collect user feedback after activities
- **Counselor Services**: Browse and connect with mental health professionals
- **User Settings**: Manage account settings, change password, and profile
- **Account Deletion**: Full CRUD operations including account deletion with related data cleanup
- **Responsive Design**: Beautiful nature-themed UI with animated floating leaves and custom cursor

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

### Page Routes

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
| `/settings` | GET | Student settings page |
| `/settings-professor` | GET | Professor settings page |
| `/resources` | GET | Student resources page |
| `/resources-professor` | GET | Professor resources management |
| `/book-appointment` | GET | Book appointment page |
| `/student-appointments` | GET | Student's appointments |
| `/my-appointments` | GET | Professional's appointments |
| `/support-classifier` | GET | AI support classifier page |
| `/more-info` | GET | Information page |

### Authentication API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/login/student` | POST | Student login API |
| `/api/login/professional` | POST | Professional login API |
| `/register` | POST | Student registration API |
| `/api/register/professional` | POST | Professional registration API |
| `/api/verify-token` | GET | Verify JWT token (protected) |

### User Management API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/student/update` | PUT | Update student profile (protected) |
| `/api/professional/update` | PUT | Update professional profile (protected) |
| `/api/student/change-password` | PUT | Change student password (protected) |
| `/api/professional/change-password` | PUT | Change professional password (protected) |
| `/api/student/delete` | DELETE | Delete student account + related data (protected) |
| `/api/professional/delete` | DELETE | Delete professional account + related data (protected) |

### Appointments API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/appointments` | GET | Get user's appointments (protected) |
| `/api/appointments` | POST | Create new appointment (protected) |

### Resources API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/resources` | GET | Get all resources |
| `/api/resources` | POST | Add resource (professionals only) |
| `/api/resources/pdfs` | GET | Get PDF resources |
| `/api/resources/videos` | GET | Get video resources |
| `/api/resources/upload-pdf` | POST | Upload PDF resource (professionals only) |
| `/api/resources/add-video` | POST | Add video resource (professionals only) |
| `/api/resources/<id>` | PUT | Update resource (professionals only) |
| `/api/resources/<id>` | DELETE | Delete resource (professionals only) |

### Event Images API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/events/images` | GET | Get all event images |
| `/api/events/upload-image` | POST | Upload event image (professionals only) |
| `/api/events/images/<id>` | DELETE | Delete event image (professionals only) |
| `/api/events/images/<id>/order` | PUT | Update image order (professionals only) |

### AI Classifier API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/classify` | POST | Classify student message (protected, students only) |

### Feedback API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/feedback/status` | GET | Check feedback status (protected) |
| `/api/feedback/track-activity` | POST | Track user activity (protected) |
| `/api/feedback/submit` | POST | Submit feedback (protected) |
| `/api/feedback/dismiss` | POST | Dismiss feedback popup (protected) |
| `/api/feedback/all` | GET | Get all feedback (professionals only) |

### Other API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/support-ticket` | POST | Create support ticket (protected) |
| `/api/notifications` | GET | Get user notifications (protected) |
| `/api/notifications/<id>/read` | PUT | Mark notification as read (protected) |
| `/students` | GET | Get all students (debug endpoint) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | MongoDB Atlas connection string |
| `JWT_SECRET_KEY` | Secret key for JWT token signing |
| `OPENAI_API_KEY` | OpenAI API key for AI classifier (optional) |

## Security Features

- **Password Hashing**: All passwords are hashed using scrypt with a 16-byte random salt
- **Password Change Verification**: Must verify current password before allowing password change
- **JWT Authentication**: Stateless authentication with 24-hour token expiration
- **HTTP-Only Cookies**: Tokens stored in HTTP-only cookies to prevent XSS attacks
- **TLS Encryption**: Secure connection to MongoDB Atlas
- **Role-Based Access Control**: Different endpoints for students and professionals

## Database Collections

The application uses MongoDB with the following collections:

| Collection | Description |
|------------|-------------|
| `students` | Student accounts and profiles |
| `professionals` | Professional/counselor accounts |
| `appointments` | Scheduled appointments |
| `resources` | PDFs and videos uploaded by professionals |
| `support_tickets` | Classified support messages |
| `notifications` | User notifications |
| `event_images` | Homepage slider images |
| `feedback` | User feedback submissions |

## Recent Updates

### Password Management (Latest)
- Added **Change Password** functionality for both students and professionals
- Password change requires verification of current password
- New passwords are hashed with scrypt before storage
- Added **show/hide password toggle** (eye icon) in password input fields

### Full CRUD Operations
- **Create**: User registration, appointments, resources, feedback
- **Read**: View profiles, appointments, resources, notifications
- **Update**: Edit profile, change password, update resources
- **Delete**: Account deletion with cascading delete of related data

## Authors

- Mental Health Support Team

## License

This project is for educational purposes.

