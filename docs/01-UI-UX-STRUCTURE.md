# UI/UX Structure

## 1. Design Goal

Create a modern, clean enterprise desktop interface that is easy for HR
staff, supervisors, administrators, and kiosk users.

## 2. Main Shell

``` text
┌─────────────────────────────────────────────────────┐
│ Sidebar              │ Topbar                       │
│                      │                              │
│ Dashboard            │ Page Header                  │
│ Workforce            ├──────────────────────────────┤
│ Biometrics           │                              │
│ Attendance           │       Page Content            │
│ Scheduling           │                              │
│ Leave                │                              │
│ Overtime             │                              │
│ Reports              │                              │
│ Administration       │                              │
└─────────────────────────────────────────────────────┘
```

## 3. Navigation

-   Dashboard
-   Workforce
    -   Employees
    -   Departments
    -   Positions
-   Biometrics
    -   Enrollment
    -   Devices
    -   Synchronization
-   Attendance
    -   Live Attendance
    -   Records
    -   Corrections
    -   Daily Summary
-   Scheduling
    -   Shift Templates
    -   Employee Schedules
    -   Calendar
    -   Holidays
-   Leave
    -   Requests
    -   Approvals
    -   Leave Types
-   Overtime
    -   Requests
    -   Approvals
-   Reports
-   Administration
    -   Users
    -   Roles & Permissions
    -   Audit Logs
    -   System Settings
    -   Database Backup

## 4. Color System

-   Primary: `#6B352A`
-   Accent: `#FFF1A6`
-   Background: `#F8F7F4`
-   Surface: `#FFFFFF`
-   Text: `#292522`
-   Muted: `#77716C`
-   Success: `#3F7D58`
-   Warning: `#C58A24`
-   Danger: `#B94A48`

Use clay brown for primary navigation and actions. Use soft butter as an
accent/highlight rather than as the dominant background.

## 5. Reusable Components

-   AppShell
-   Sidebar
-   TopBar
-   PageHeader
-   StatCard
-   DataTable
-   SearchBox
-   FilterDropdown
-   StatusBadge
-   ModalDialog
-   ConfirmationDialog
-   ToastNotification
-   LoadingIndicator
-   EmptyState
-   ErrorState
-   EmployeeAvatar
-   AttendanceTimeline

## 6. UX Rules

-   Avoid destructive actions without confirmation.
-   Never silently overwrite biometric attendance history.
-   Use clear status badges.
-   Provide empty, loading, error, and success states.
-   Keep kiosk mode extremely simple.
-   Use consistent forms and validation.
