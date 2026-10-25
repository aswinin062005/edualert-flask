# 🎓 EduAlert - Department SMS Notification System

EduAlert is an automated web application built for college departments to process student academic mark sheets and automatically notify parents of failing students via instant SMS.

---

## 📌 Features

* **HOD Authentication**: Secure login portal for the Head of Department (HOD).
* **Excel Data Processing**: Instant parsing of `.xlsx` and `.xls` marksheets using Pandas.
* **Automated Failure Detection**: Automatically identifies students scoring below passing criteria (< 50 marks).
* **Real-time SMS Integration**: Dispatches mobile text alerts to parents via Fast2SMS API.
* **Live Audit Log**: Displays a dispatch log on the dashboard with real-time delivery statuses (*Sent*, *Failed*, *Simulated*).
* **Responsive UI**: College-themed dashboard built with Bootstrap 5 and custom styling.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.x, Flask
* **Data Processing**: Pandas, Openpyxl
* **SMS Gateway**: Fast2SMS API (`requests`)
* **Frontend**: HTML5, CSS3, Bootstrap 5, Bootstrap Icons

---

## 📁 Project Directory Structure

```text
EduAlert_Project/
│
├── app.py                      # Main Flask application logic & routes
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation & setup guide
│
├── static/
│   └── college.jpg             # Campus background image
│
└── templates/
    ├── login.html              # HOD Login page template
    └── dashboard.html          # Department dashboard template