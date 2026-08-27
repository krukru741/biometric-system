# Authentication and Authorization

## 1. Goal

Secure access to the application using accounts, roles, permissions,
session control, password hashing, and audit logging.

## 2. Login Flow

``` text
Login
  ↓
Validate Credentials
  ↓
Check Account Status
  ↓
Load User Roles
  ↓
Load Permissions
  ↓
Create Session
  ↓
Dashboard
```

## 3. Login UI

Fields:

-   Username
-   Password
-   Show/hide password
-   Sign In
-   Forgot Password

## 4. Roles

### Administrator

Full system access.

### HR

-   Employees
-   Attendance
-   Schedules
-   Leave
-   Overtime
-   Reports

### Supervisor

-   Team attendance
-   Leave approval
-   Overtime approval
-   Team reports

### Kiosk

-   Biometric attendance only

## 5. Permission Naming

Use granular permissions:

``` text
dashboard.view

employee.view
employee.create
employee.edit
employee.archive

attendance.view
attendance.correct
attendance.approve
attendance.kiosk

biometric.enroll
biometric.manage

schedule.view
schedule.create
schedule.edit

leave.view
leave.create
leave.approve

overtime.view
overtime.create
overtime.approve

reports.view
reports.export

users.manage
settings.manage
audit.view
backup.manage
```

`attendance.kiosk` scopes an account to biometric attendance capture only,
consistent with the Kiosk role in Section 4. It should not carry any
other view/edit permissions.

## 6. Dashboard Access vs. Quick Actions

`dashboard.view` only controls whether the dashboard page itself is
visible. It must **not** implicitly grant access to any of the dashboard's
quick actions. Each quick action checks its own module permission
independently:

``` text
dashboard.view
      ↓
Dashboard visible

Add Employee        → employee.create
Enroll Biometric     → biometric.enroll
View Attendance       → attendance.view
Review Leave         → leave.approve
Review Overtime      → overtime.approve
```

A user with `dashboard.view` but without `employee.create` must not see
(or must not be able to use) the "Add Employee" quick action. This keeps
the dashboard from becoming a permission bypass.

## 7. Security

-   Hash passwords using a strong password hashing algorithm.
-   Never store plaintext passwords.
-   Use parameterized database operations / SQLAlchemy ORM.
-   Apply authorization at the service layer, not only in the UI.
-   Expire inactive sessions.
-   Log security-sensitive actions.
