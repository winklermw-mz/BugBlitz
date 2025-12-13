# 🐞 BugBlitz - Test Management System

BugBlitz is a lightweight, role-based web application for managing test projects, test cases, and test runs. Built with Flask and SQLAlchemy, it provides a streamlined interface for defining test specifications and documenting execution results.

## Features

This application includes advanced features for comprehensive test management:

### Flexible Role Management

Users can be assigned multiple roles, allowing for complex permission structures.

- Administrator: Full CRUD (create, read, update, delete) access across all data sets.
- Test Manager: Can create and manage projects, cases, and test runs, and is responsible for run lifecycle management. Can also act as a tester.
- Tester: Primary role is to execute assigned test cases and log results.

### Test Case Specification

- Custom Attributes: Test cases include fields for title, summary, pre/post conditions, priority (high/medium/low), and source.
- Hashtags: Support for defining descriptive tags (hashtags) per test case. New tags can be created on-the-fly, and existing ones can be selected via autocomplete.
- Manual Ordering: Test cases within a Project can be manually sorted using up/down buttons for defining a logical execution sequence, overriding standard sorting.
- Step Management: Test steps can be easily added, deleted, and reordered (up/down movement) within the test case definition.
- AI Assistent Creation: Test Cases can automatically be derived from provided requirements using a LLM service.

### Test Run & Assignment

- Bulk Assignment: During test run planning, test cases can be assigned to one or more testers individually or in bulk.
- Run Lifecycle: Managers/admins can control the state of a test run: `active`, `finished`, or `aborted`. An aborted/finished run can be re-opened to active status.

### Execution and Reporting

- Aggregated Status View: The test execution mask provides an aggregated status dashboard displaying the total number of cases, along with counts for OK, Failed, Blocked, and Not Tested.
- Granular Step Results: Testers can optionally document the result (`ok`, `blocked`, `failed`, `not tested`) and a short comment for individual test steps. This detail view is collapsible/hidden by default to maintain a clean interface.

### Data Cleanup

- Deletion: Authorized users (admins/managers) have the ability to delete test projects, test cases, and test runs, ensuring data can be cleanly maintained.

## Installation & Setup

### Prerequisites

- Python 3.12

### Installation Steps

1.  Clone the Repository (or save the files): Ensure you have `app.py` and the `templates/` directory structure.
2.  Create a Virtual Environment (Recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install Dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Set the following environment variables if the AI service is used. Modify these default values if necessary.
    ```bash
    export LLM_HOST=http://localhost:1234/v1
    export LLM_API_KEY=lm-studio
    export LLM_MODEL=qwen/qwen3-vl-4b
    ```
5.  Run the Application:
    ```bash
    python app.py
    ```
    The application will be accessible at `http://127.0.0.1:8003/`.

## Initial Credentials

Upon the first startup, the application creates a default administrative user:

| Role | Username | Password |
| :--- | :--- | :--- |
| Admin, manager, tester | admin | admin |

## Contributing

BugBlitz is intended as a feature-rich prototype. Feel free to extend its functionality, integrate advanced reporting, or enhance the user interface!
