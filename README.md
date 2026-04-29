# Jane Mahloo Student Accommodation System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PHP](https://img.shields.io/badge/PHP-7.4+-blue.svg)](https://www.php.net/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-purple.svg)](https://www.postgresql.org/)

## 🚀 Live Demo
**Landing Page**: [1st.html](1st.html) - Showcases accommodation for NSFAS/UL students with slideshow, features (safe, furnished, near campus), requirements (ID, registration proof, NSFAS funding).

## 🎯 Project Overview
**Jane Mahloo Student Accommodation** is a **full-stack web application** for managing student housing at University of Limpopo (UL). It handles room applications, document verification, payments, ratings, announcements, and admin management.

### Key Features

#### **Student Dashboard** (`student_dashboard.php`)
- **Room Applications**: Apply for Room Option 1 (R4500, ground/1st floor) or Option 2 (R4000, 2nd/3rd floor). View availability stats.
  ```php
  // Room stats query example
  $count_sql = "SELECT COUNT(*) as available FROM room_option_1 WHERE floor_number = $1 AND occupied = 'no'";
  ```
- **Profile Management**: Edit details, upload profile picture (`Pictures/student_[ID].jpg`).
- **Supporting Documents**: Upload ID/PoR/PoF as PDF (`table/[ID]_[TYPE].pdf`).
- **NSFAS Payment Status**: Track paid/outstanding.
- **Announcements**: View residence updates, mark as read (`student_announcement_views`).
- **Residence Ratings**: Submit 1-5 stars + comments per semester (`residence_ratings` table). Overall avg displayed.
- **Modern UI**: Image slideshows, responsive sidebar navigation.

#### **Admin Dashboard** (`admin_dashboard.php`)
- **Dashboard Analytics**: Cards for students/payments/visitors/applications/registrations/rooms/announcements.
  - Charts: Payment pie (paid/outstanding), announcement viewers.
  - Recent ratings widget (like Google reviews).
- **Students Management**: View registered/all students, unblock accounts.
- **Applications**: Review/update status (Pending→Approved→Registered/Cancelled).
- **Visitors**: Log in/out times.
- **Payments**: Track NSFAS paid/outstanding students.
- **Announcements**: Create/post to registered students.

#### **Authentication** (`login.php` / `signup.html`)
- **Student Signup**: Strict validation (9-digit ID, names letters-only, SA phone 0xxxxxxxx, strong PW).
- **Dual Login**: Student/Manager with attempt locking.
- **Password Reset**: 6-digit PIN email verification.

#### **Backend & Database**
- **PostgreSQL** (`NewDbConn.php`): Tables for `student`, `applications`, `residence_manager`, `payment`, `Visitor`, `residence_ratings`, `announcements`, `supporting_documents`.
- **Security**: Prepared statements (`pg_query_params`), password_hash, session auth, file upload validation (PDF<1MB).

## 🏗️ Tech Stack
```
Frontend: HTML5/CSS3/JS, FontAwesome, Chart.js
Backend: PHP 7.4+
Database: PostgreSQL 13+
Hosting: XAMPP (Apache/MySQL ready, but uses PG)
AI/ML: SAMS Chatbot (Chatbot/ folder), Payment Risk Prediction (Model/)
```
**SAMS Chatbot**: Integrated on landing page - handles payments/rules/visitors/applications.

## 🚀 Quick Start (Local)

### 1. Prerequisites
```
- XAMPP (Apache + PostgreSQL)
- PHP 7.4+
- Composer (optional for deps)
```

### 2. PostgreSQL Setup
```bash
# Create DB & tables (SQL/ folder)
psql -U postgres -f SQL/Jane_Maahlo.sql
# Insert test data
psql -d Jane_Maahlo -f SQL/insert_students.sql
psql -d Jane_Maahlo -f SQL/Residence_manager.sql
```

Update `NewDbConn.php`:
```php
$connection = pg_connect("host=localhost dbname=Jane_Maahlo user=postgres password='YOUR_PASS'");
```

### 3. File Structure
```
c:/xampp/htdocs/New folder/
├── 1st.html (Landing)
├── signup.html + signup.php
├── login.php
├── student_dashboard.php
├── admin_dashboard.php
├── Pictures/ (Room images/profiles)
├── table/ (Student docs PDFs)
├── Chatbot/ (SAMS AI Assistant)
├── SQL/ (DB Schema)
└── Model/ (ML Payment Prediction)
```

### 4. Run
```
# htdocs/New folder/
http://localhost/New%20folder/1st.html
```

**Default Login**:
- **Student**: 123456789 / password
- **Manager**: 1 / password

## 📁 Screenshots
**Student Home** (Room Options Slideshow):
![Student Dashboard](Pictures/S%201.jpg)

**Admin Analytics**:
- Payment pie chart, ratings widget, room availability.

**Ratings System**:
```
Overall: 4.2/5 (127 reviews)
Semester filter: 1st/2nd
```

## 🛠️ Room Details
| Option | Price | Floors | Features |
|--------|-------|--------|----------|
| 1 | R4500 | 0-1 | Bed, desk, wardrobe, shared kitchen/toilets/elevator |
| 2 | R4000 | 2-3 | Same amenities |

**Application Flow**: Apply → Admin Approve → Upload Docs → Pay NSFAS → Register Room.

## 🤖 AI Features
1. **SAMS Chatbot**: Live on landing (`Chatbot/chat_endpoint.php`) - Answers via local ML model.
2. **Payment Risk ML**: Predicts default risk (`Model/SAMS_Payment_Risk_Prediction.py`).

## 📈 Database Schema (Key Tables)
```sql
student(student_number PK, fname, password, blocked)
applications(application_id PK, student_number, status)
residence_ratings(id PK, stars, comment, semester)
payment(student_number PK, payment_date)
announcements(announcement_id PK, manager_id, title, content)
supporting_documents(document_id PK, student_number, document_type, file_path)
```

## 🔒 Security
- SQL injection: `pg_query_params`
- File uploads: PDF-only, size-limit, safe names
- Auth: PHP sessions + hash_verify + brute-force lock
- XSS: `htmlspecialchars()`

## 📱 Responsive
- Mobile-first: Sidebar collapses, charts responsive.

## 🤝 Contributing
1. Fork repo
2. `git checkout -b feature/xyz`
3. Commit & PR to `main`

## 📄 License
MIT - Free for educational/portfolio use.

## 🙏 Acknowledgments
Built for University of Limpopo (UL) NSFAS students.
Inspired by modern hostel management systems.

**⭐ Star if helpful! 🚀**

---
**Live Features**:
- [ ] Payment gateway integration
- [ ] Visitor QR check-in
- [ ] Mobile PWA

