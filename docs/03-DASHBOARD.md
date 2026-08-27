# Dashboard

## 1. Goal

The dashboard should immediately answer:

> What is happening with attendance today?

## 2. Header

Display:

-   Greeting
-   Current date
-   Current time
-   Current logged-in user

## 3. KPI Cards

Recommended cards:

-   Total Employees
-   Present
-   Absent
-   Late
-   On Leave
-   Overtime

## 4. Attendance Summary

Display a visual breakdown of:

-   Present
-   Late
-   Absent
-   Leave
-   Rest Day
-   Holiday

## 5. Recent Attendance

Columns:

-   Time
-   Employee
-   Employee ID
-   Event
-   Device
-   Status

Example:

``` text
08:02 AM  Juan Dela Cruz  EMP-001  IN   Main Entrance
08:07 AM  Maria Santos    EMP-002  IN   Main Entrance
08:15 AM  Pedro Garcia    EMP-003  IN   Main Entrance
```

## 6. Alerts

Show important operational issues:

-   Biometric device offline
-   Pending leave approvals
-   Pending overtime approvals
-   Incomplete attendance
-   Synchronization errors

## 7. UX

Dashboard should be read-only by default, with quick actions for:

-   Add Employee
-   Enroll Biometric
-   View Attendance
-   Review Requests

## 8. Permissions

Viewing the dashboard requires `dashboard.view`. This permission only
controls page visibility — it does **not** grant access to any quick
action. Each quick action is independently gated by its own module
permission (see `02-AUTHENTICATION-AUTHORIZATION.md`, Section 6):

| Quick Action      | Required Permission |
|-------------------|----------------------|
| Add Employee      | `employee.create`    |
| Enroll Biometric  | `biometric.enroll`   |
| View Attendance   | `attendance.view`    |
| Review Requests   | `leave.approve` and/or `overtime.approve` |

A quick action should be hidden (or disabled) if the current user lacks
the corresponding permission, even if they can see the dashboard itself.
