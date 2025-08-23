# TAR UMT Student Assistant Application

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-Academic-brightgreen)

-----

# Student Assistant Program

Welcome to the **Student Assistant Program**\! This is your all-in-one desktop toolkit designed to boost productivity, manage your academic life, and help you stay organized. This application suite is built with Python and Tkinter, providing a modern, intuitive, and responsive user interface.

## 🌟 Core Features

  - **Centralized Hub**: A beautiful main dashboard to launch all your productivity tools.
  - **Multiple Tools in One**: Access four powerful applications from a single launcher.
  - **Modern UI**: A visually appealing interface with light and dark themes, hover effects, and a clean layout.
  - **Persistent Data**: Your tasks, settings, and academic data are saved locally, so you never lose your progress.
  - **Cross-Platform**: Built with Python's standard library, making it compatible with Windows, macOS, and Linux.

-----

## 🛠️ Included Tools

The Student Assistant Program includes the following integrated applications:

### 1\. ⏱️ Pomodoro Timer

A feature-rich focus timer based on the Pomodoro Technique to help you manage your study sessions effectively.

  - **Flexible Timer Modes**: Switch between Pomodoro (25 mins), Short Break (5 mins), Long Break (15 mins), and a continuous Stopwatch mode.
  - **Task Management**: A built-in to-do list where you can add, delete, and prioritize tasks.
  - **Customizable Sessions**: Adjust timer durations and the interval for long breaks in the settings.
  - **Daily Goals**: Set a primary goal for the day to stay motivated.
  - **Audio Alerts**: Get notified with a sound when a session ends. You can use the default sound or choose your own `.wav` or `.mp3` file.
  - **Themes**: Toggle between a sleek dark mode and a clean light mode.
  - **Motivational Quotes**: Get a dose of inspiration at the start of each Pomodoro session.

### 2\. 📚 Homework Planner

An elegant and powerful tool to organize all your homework assignments and academic tasks.

  - **Detailed Task Entry**: Add tasks with fields for **Subject**, **Title**, **Deadline**, **Priority** (High, Medium, Low), and **Notes**.
  - **Smart Task Sorting**: The task list automatically sorts by completion status, deadline, and priority, so you always know what to work on next.
  - **Edit Mode**: Easily load any task back into the input form to make changes.
  - **Status Tracking**: Mark tasks as "Done" or "Not Done" to track your progress. The "Done" tasks are visually distinguished and moved to the bottom of the list.
  - **Data Persistence**: All your homework tasks are saved to a `homework.json` file, so your planner is always up-to-date.

### 3\. 📊 GPA Calculator

A modern and user-friendly calculator to track your Grade Point Average with ease.

  - **Course Management**: Add courses with details for course name, credit hours, and grade.
  - **Real-Time Calculation**: Your GPA is instantly updated as you add, edit, or remove courses.
  - **Data Import/Export**: Save your course list to a `.csv` file for your records or load an existing list to continue where you left off.
  - **Interactive Editing**: Double-click any course in the list to open a pop-up window and edit its details.
  - **Light & Dark Themes**: Switch between themes to match your preference.

### 4\. 🗓️ Reminder App

A robust reminder system to ensure you never miss an important deadline, event, or task.

  - **Custom Reminders**: Set reminders with a title, a detailed message, and a precise due date/time.
  - **Recurring Options**: Configure reminders to repeat **Daily**, **Weekly**, or **Monthly**.
  - **Audio Alerts**: Get persistent audio notifications when a reminder is due. You can use the default system sound or select your own custom `.wav` or `.mp3` file.
  - **Enable/Disable**: Temporarily disable reminders without deleting them.
  - **Rich User Interface**: A detailed table view shows all your reminders, which can be sorted and filtered.
  - **Quick Actions**: Use keyboard shortcuts, right-click context menus, or click directly on the table to quickly edit, delete, or toggle reminders.

-----

## 🚀 How to Run the Application

1.  **Prerequisites**: Ensure you have **Python 3** installed on your system.
2.  **Install Dependencies**: This application may have dependencies like `pygame`. You can install them using pip:
    ```sh
    pip install pygame
    ```
3.  **Launch the Hub**: Run the `main.py` script to open the central dashboard.
    ```sh
    python main.py
    ```
4.  **Open Tools**: From the dashboard, click on any of the application cards to launch the desired tool. Each tool will open in its own window, and you can use multiple tools simultaneously.

## 📁 File Structure

  - **`main.py`**: The main launcher for the Student Assistant dashboard.
  - **`pomodoro_timer.py`**: The Pomodoro Timer application.
  - **`gpa_calculator.py`**: The GPA Calculator application.
  - **`reminder_app.py`**: The Reminder App application.
  - **`home_planner.py`**: The Homework Planner application.
  - **`/data/`** (directory): This folder is automatically created to store all application data, including settings, tasks, and reminders.
      - `pomodoro_data.json`: Stores data for the Pomodoro Timer.
      - `homework.json`: Stores data for the Homework Planner.
      - `gpa_config.json`: Stores the theme setting for the GPA Calculator.
      - `reminders.db`: A SQLite database for the Reminder App.
      - Saved `.csv` files from the GPA calculator will also be stored here.

-----

Enjoy using the Student Assistant Program\! 🎉

## Academic Integrity Statement
> We declare that this assignment is our own work except where due acknowledgment is made. We have followed TAR UMT's Plagiarism Policy and confirm that this work is original. All group members have contributed substantially to the development of this application.

## Submission Information
- **Assignment Deadline**: September 14, 2025 (Sunday of Week 12), before 12:00am
- **Course**: AMCS1034 Software Development Fundamentals

---

*This project was developed as part of the AMCS1034 Software Development Fundamentals course requirements at TAR UMT.*


