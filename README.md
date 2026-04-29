# Jarrelix Student Accommodation System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PHP](https://img.shields.io/badge/PHP-7.4+-blue.svg)](https://www.php.net/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-purple.svg)](https://www.postgresql.org/)

## 🎯 Project Overview
**Jarrelix Student Accommodation** is a **full-stack web application** for managing student housing at any university. It handles room applications, document verification, payments, ratings, announcements, and admin management.

## 💡 Problems & Solutions

| **Problem** | **Traditional Manual Process** | **Jarrelix Solution** |
|-------------|--------------------------------|--------------------------|
| **Room Allocation Conflicts** | Manual paper forms, no real-time availability, double-booking | Automated applications w/ live room stats per floor/option (`student_dashboard.php`), status workflow (Pending→Approved→Registered/Cancelled) (`application_process.php`) |
| **NSFAS Payment Verification** | Manual receipt checking, no tracking | Payment logging (`add_payment.php`), status tracking (Paid/Outstanding), admin dashboard pie charts (`admin_dashboard.php`) |
| **Document Verification Delays** | Physical submission, lost docs | Secure PDF uploads (ID/PoR/PoF <1MB to `table/`) (`student_dashboard.php`), admin review |
| **Poor Communication** | Notice boards, missed updates | Manager→registered students announcements w/ individual view tracking (`student_announcement_views`) |
| **No Feedback System** | No structured ratings | Semester-based 1-5★ ratings + comments (`residence_ratings`), overall avg + recent widget |
| **Security & Access Issues** | Weak auth, no blocking | Strict signup validation (`signup.php`), dual-role login w/ brute-force block/reset (`login.php`) |
| **Visitor Management** | Manual logbook | Digital in/out timestamps per student (`Visitor` table, `admin_dashboard.php`) |
| **Admin Oversight** | Spreadsheets, no analytics | Unified dashboard w/ cards/charts/search/pagination (`admin_dashboard.php`) |

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

## 🙏 Acknowledgments
Built for University students that uses NSFAS.
Inspired by modern hostel management systems.

**⭐ Star if helpful! 🚀**

---
**Live Features**:
- [ ] Payment gateway integration
- [ ] Visitor QR check-in
- [ ] Mobile PWA

