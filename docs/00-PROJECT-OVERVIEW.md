# Biometric Attendance Tracking System --- Project Overview

## 1. Purpose

A Python-based biometric attendance tracking system for managing employees,
biometric identity, attendance events, schedules, leave, overtime,
reports, users, permissions, audit logs, and database administration.

## 2. Recommended Stack

-   Python 3.11+
-   PySide6 (Qt for Python)
-   MVVM (adapted for PySide6 using Signals/Slots)
-   SQLAlchemy 2.0 (ORM) + Alembic for migrations
-   SQLite
-   Biometric SDK/device integration (vendor SDK via Python bindings / ctypes)
-   ReportLab or WeasyPrint for PDF reports
-   openpyxl for Excel export
-   dependency-injector for Dependency Injection
-   structlog (or standard `logging`) for structured logging

## 3. High-Level Architecture

``` text
PySide6 UI (Views)
  ↓
ViewModels (QObject + Signals/Slots)
  ↓
Application Services
  ↓
Domain/Core
  ↓
Repositories / SQLAlchemy
  ↓
SQLite

Biometric Device
  ↓
Biometric Service / Adapter
  ↓
Attendance Event
  ↓
Attendance Processing Engine
  ↓
Attendance Record
```

## 4. Core Modules

1.  Authentication and Authorization
2.  Dashboard
3.  Workforce / Employees
4.  Biometrics
5.  Attendance
6.  Scheduling
7.  Leave
8.  Overtime
9.  Reports
10. Administration
11. Audit Logging
12. Backup and Restore

## 5. Primary Design Principle

The biometric device should identify **who scanned and when**. The
attendance engine should determine **what that scan means**.

This keeps biometric integration independent from attendance rules and
allows different scanner brands to be supported later.
