# Database Schema

## 1. Core Tables

``` text
Users
Roles
Permissions
UserRoles
RolePermissions

Employees
Departments
Positions

BiometricDevices
EmployeeBiometrics
BiometricLogs

AttendanceEvents
AttendanceRecords
AttendanceCorrections

ShiftTemplates
EmployeeSchedules
Holidays

LeaveTypes
LeaveRequests
LeaveBalances

OvertimeRequests

AuditLogs
SystemSettings
```

## 2. Employee Relationships

``` text
Employee
 ├── Department
 ├── Position
 ├── EmployeeBiometrics
 ├── EmployeeSchedules
 ├── AttendanceEvents
 ├── AttendanceRecords
 ├── LeaveRequests
 └── OvertimeRequests
```

## 3. Recommended Keys

Every primary entity should have a stable primary key.

Use foreign keys for relationships and indexes for frequently queried
fields.

## 4. Important Indexes

Recommended indexes:

-   Employees.EmployeeId
-   Employees.DepartmentId
-   AttendanceEvents.EmployeeId + Timestamp
-   AttendanceRecords.EmployeeId + Date
-   EmployeeSchedules.EmployeeId + Date
-   LeaveRequests.EmployeeId + StartDate
-   OvertimeRequests.EmployeeId + Date
-   AuditLogs.Timestamp
-   BiometricDevices.Status

## 5. Data Integrity

Use:

-   Foreign keys
-   Unique constraints
-   Required fields
-   Valid status enums
-   Transaction boundaries
-   Soft delete/archive where historical data must remain

## 6. Biometric Data

Do not store raw biometric images unless required by the device/SDK and
policy.

Prefer encrypted biometric templates.

## 7. Attendance Architecture

Separate:

``` text
Raw biometric events
        ↓
Processed attendance records
        ↓
Reports
```

This preserves traceability.

## 8. Cross-References

Full field-level entity schemas for the following core tables are defined
in their respective module documents, not repeated here in full, to avoid
drift between documents:

-   `AttendanceCorrections` → see `06-ATTENDANCE.md`, Section 7.1
-   `BiometricDevices`, `BiometricLogs` → see `05-BIOMETRICS.md`, Section 6

Both follow the same traceability principle as Section 7 above: original
biometric events and device logs are never overwritten, only layered with
corrections/derived records that reference back to them.
