# Library Management System

## Table of Contents
1. [About the Project](#about-the-project)
2. [Features](#features)
3. [Technologies Used](#technologies-used)
4. [Installation](#installation)
5. [Usage](#usage)

### About the Project
The Library Management System is a web-based application designed to simplify the management of library operations. It provides librarians and users with an intuitive platform to track, manage, and borrow books while ensuring a seamless experience. This system eliminates the need for using files or register to save the record and makes the process of managing resources efficient and error-free.

### Features
- **User Authentication**: 
  - Secure user registration and login.
  - Password reset functionality.

- **Book Management**:
  - Add, update, delete, and view book details.
  - Organize books by categories or genres.

- **Borrowing System**:
  - It let's user to borrow books with a due date.
  - The system notifies users of overdue books.

- **Search Functionality**:
  - Search by title, author, ISBN, or genre.
  - Advanced filtering options.

- **Responsive Design**:
  - Optimized for all devices (desktop, tablet, mobile).

- **Admin Dashboard**:
  - Manage user roles and permissions.
  - View borrowing history.


## Technologies Used

- **Backend**: Python, Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: MySQL
- **Version Control**: Git


### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Library-Management-System.git
2. Navigate to project repo
   ```bash
   cd library-management-system
2. Create a virtual environment
   ```bash
   python3 -m venv venv
   venv\Scripts\activate
4. Install dependencies
   ```bash
   pip install -r requirements.txt
5. Set up the database
   ```bash
   py manage.py migrate
6. Run the development server
   ```bash
   py manage.py runserver
7. Access the application at http://127.0.0.1:8000


### Usage
1. Register or log in to access the system.
2. Browse the library catalog or search for books.
3. Librarian can borrow you borrow a book based on availability.
4. Administrators can log in to the admin panel to manage resources.


