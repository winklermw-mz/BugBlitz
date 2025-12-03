# 🐞 BugBench - Test Management System (Flask/SQLAlchemy)

BugBench is a lightweight, role-based web application for managing Test Projects, Test Cases, and Test Runs. Built with **Python Flask** and **SQLAlchemy**, it provides a streamlined interface for defining test specifications and documenting execution results, supporting both light and dark themes.

---

## ✨ Features

This application includes advanced features for comprehensive test management:

### 1. 👥 Flexible Role Management

Users can be assigned multiple roles, allowing for complex permission structures.
* **Administrator (Admin):** Full CRUD (Create, Read, Update, Delete) access across all data sets (Users, Projects, Cases, Runs).
* **Test Manager (Manager):** Can create and manage Projects, Cases, and Test Runs, and is responsible for run lifecycle management. Can also act as a Tester.
* **Tester:** Primary role is to execute assigned Test Cases and log results.

### 2. 📝 Test Case Specification

* **Custom Attributes:** Test Cases include fields for Title, Summary, Pre/Post Conditions, Priority (High/Medium/Low), and Source.
* **Hashtags/Tags:** Support for defining descriptive tags (hashtags) per Test Case. New tags can be created on-the-fly, and existing ones can be selected via autocomplete.
* **Manual Ordering:** Test Cases within a Project can be manually sorted using **Up/Down buttons** for defining a logical execution sequence, overriding standard sorting.
* **Step Management:** Test Steps can be easily added, deleted, and reordered (up/down movement) within the Test Case definition.

### 3. 🏃 Test Run & Assignment

* **Bulk Assignment:** During Test Run planning, Test Cases can be assigned to **one or more** Testers individually or in bulk.
* **Run Lifecycle:** Managers/Admins can control the state of a Test Run: `active`, `finished`, or `aborted`. An aborted/finished run can be **re-opened** to active status.

### 4. ✅ Execution and Reporting

* **Aggregated Status View:** The Test Execution Mask provides an aggregated status dashboard displaying the total number of cases, along with counts for **OK**, **Failed**, **Blocked**, and **Not Tested**.
* **Granular Step Results:** Testers can optionally document the result (`ok`, `blocked`, `failed`, `not tested`) and a short comment for **individual Test Steps**. This detail view is collapsible/hidden by default to maintain a clean interface.

### 5. 🗑️ Data Cleanup

* **Deletion:** Authorized users (Admins/Managers) have the ability to delete Test Projects, Test Cases, and Test Runs, ensuring data can be cleanly maintained.

---

## 🛠️ Installation & Setup

### Prerequisites

* Python 3.x
* `pip` (Python package installer)

### Installation Steps

1.  **Clone the Repository (or save the files):**
    Ensure you have `app.py` and the `templates/` directory structure.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug
    ```

4.  **Database Initialization:**
    **⚠️ IMPORTANT:** Due to schema changes (Roles, Tags, Sequences), you may need to delete the existing database file (`bugbench.db`) before the first run to ensure the new tables and fields are created correctly.

5.  **Run the Application:**
    ```bash
    python app.py
    ```
    The application will be accessible at `http://127.0.0.1:5000/`.

---

## 🔑 Initial Credentials

Upon the first startup, the application creates a default administrative user:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin, Manager, Tester** | `admin` | `admin` |

---

## 🤝 Contributing

BugBench is intended as a feature-rich prototype. Feel free to extend its functionality, integrate advanced reporting, or enhance the user interface!