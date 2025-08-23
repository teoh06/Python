# TAR UMT Student Assistant Application

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-Academic-brightgreen)

## Overview
This application is a comprehensive Student Assistant tool developed for the **AMCS1034 Software Development Fundamentals** assignment. It integrates four essential features designed to help TAR UMT students manage their academic responsibilities more effectively. The application is built entirely in Python, following the assignment guidelines and requirements.

## Features

### 📊 GPA Calculator
- Calculate Grade Point Average based on course grades and credit hours
- Support for different grading scales
- Visual representation of academic performance through charts
- Data persistence through file storage

### 📝 Homework Planner
- Create, organize, and prioritize homework assignments
- Set subjects, deadlines, status tracking, and detailed notes
- Categorization of tasks by subject or priority
- View pending and completed assignments

### ⏱️ Study Pomodoro Timer
- Implement the Pomodoro Technique (25-minute focused sessions)
- Customizable work/break intervals
- Session tracking and productivity metrics
- Visual and audio notifications

### 🔔 Simple Reminder App
- Set one-time or recurring reminders for classes and tasks
- Notification system for upcoming events
- Organize reminders by category
- Persistent storage of reminder data

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Standard Python libraries (included in Python installation)

### Step-by-Step Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/teoh06/Python.git
   cd [your_file_path]
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame
   ```

3. **Verify installation:**
   ```bash
   python --version
   # Should show Python 3.8+
   ```

## Usage

### Running the Application
```bash
python main.py
```

### Main Menu Navigation (Example)
Upon launching, you'll see the main menu:
```
===== TAR UMT STUDENT ASSISTANT =====
1. GPA Calculator
2. Study Pomodoro Timer
3. Simple Reminder App
4. Homework Planner (Coming Soon)
5. Exit

Please select an option (1-5):
```

Navigate using number keys and follow the on-screen instructions for each feature.

## Project Structure
```
├── main.py                # Application entry point with main menu
├── gpa_calculator.py      # GPA calculation functionality
├── pomodoro_timer.py      # Pomodoro timer implementation
├── reminder_app.py        # Reminder application logic
├── homework_planner.py    # Homework management system
├── data/                  # Persistent storage directory
│   ├── gpa_data.json
│   ├── homework_data.json
│   └── reminders_data.json
└── README.md              # Project documentation
```

## Screenshots

### Main Interface
![Main Menu](screenshots/main_menu.png) - Coming Soon

### GPA Calculator
![GPA Calculator](screenshots/gpa_calculator.png) - Coming Soon

### Homework Planner
![Homework Planner](screenshots/homework_planner.png) - Coming Soon

### Pomodoro Timer
![Pomodoro Timer](screenshots/pomodoro_timer.png) - Coming Soon

### Reminder App
![Reminder App](screenshots/reminder_app.png) - Coming Soon

## Technical Implementation

### Key Python Concepts Demonstrated
- **Control Structures**: Extensive use of if-else and match statements
- **Loops**: For and while loops for data processing
- **File Processing**: JSON storage for persistent data
- **Collections**: Lists, dictionaries, and sets for data organization
- **Functions**: Modular design with user-defined functions
- **Exception Handling**: Robust error handling throughout
- **String Processing**: Input validation and formatting
- **OOP Principles**: Encapsulation and inheritance implementation

### Dependencies
```
# requirements.txt
# (Standard libraries only - no external dependencies required)
```

## Academic Integrity Statement
> We declare that this assignment is our own work except where due acknowledgment is made. We have followed TAR UMT's Plagiarism Policy and confirm that this work is original. All group members have contributed substantially to the development of this application.

## Submission Information
- **Assignment Deadline**: September 14, 2025 (Sunday of Week 12), before 12:00am
- **Course**: AMCS1034 Software Development Fundamentals

---

*This project was developed as part of the AMCS1034 Software Development Fundamentals course requirements at TAR UMT.*
