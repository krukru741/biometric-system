# Attendance Module

## 1. Goal

Capture biometric events and transform them into reliable attendance
records.

## 2. Core Principle

Never rely only on:

``` text
EmployeeId + Date + TimeIn + TimeOut
```

Store raw attendance events first.

## 3. Attendance Event

Recommended fields:

``` text
AttendanceEvent
--------------------------
Id
EmployeeId
DeviceId
EventType
Timestamp
BiometricVerified
Source
CreatedAt
```

Possible events:

-   IN
-   OUT
-   BREAK_OUT
-   BREAK_IN

## 4. Attendance Record

``` text
AttendanceRecord
------------------------
Id
EmployeeId
ScheduleId
Date
TimeIn
BreakOut
BreakIn
TimeOut
WorkedMinutes
LateMinutes
UndertimeMinutes
OvertimeMinutes
Status
CreatedAt
UpdatedAt
```

## 5. Processing Flow

``` text
Biometric Scan
  ↓
Identify Employee
  ↓
Create Attendance Event
  ↓
Determine Event Type
  ↓
Load Schedule
  ↓
Load Leave / Holiday / Rest Day
  ↓
Apply Attendance Rules
  ↓
Calculate Minutes
  ↓
Generate Attendance Record
```

## 6. Statuses

-   PRESENT
-   LATE
-   ABSENT
-   ON_LEAVE
-   REST_DAY
-   HOLIDAY
-   HALF_DAY
-   INCOMPLETE
-   UNDERTIME
-   OVERTIME

## 7. Attendance Correction

Never overwrite the original biometric event.

Use:

``` text
Original Event
  ↓
Correction Request
  ↓
Reason
  ↓
Approval
  ↓
Adjusted Attendance Record
  ↓
Audit Log
```

### 7.1 AttendanceCorrection Entity

``` text
AttendanceCorrection
-------------------------
Id
AttendanceRecordId
EmployeeId
CorrectionType
OriginalValue
RequestedValue
Reason
AttachmentPath
Status
RequestedBy
RequestedAt
ReviewedBy
ReviewedAt
ReviewComment
CreatedAt
UpdatedAt
```

Possible `Status` values: `PENDING`, `APPROVED`, `REJECTED`.

Possible `CorrectionType` values: `TIME_IN`, `TIME_OUT`, `BREAK_OUT`,
`BREAK_IN`, `STATUS`.

### 7.2 Traceability Chain

The original biometric data must remain immutable. Corrections are
layered on top of it, never in place of it:

``` text
AttendanceEvent
      ↓
AttendanceRecord
      ↓
AttendanceCorrection
      ↓
AuditLog
```

## 8. Late Calculation

Example:

``` text
Shift: 08:00 AM
Grace: 10 minutes

Actual: 08:07
Late: 0

Actual: 08:15
Late: 15 minutes
```

## 9. Overnight Shifts

Represent schedules using DateTime ranges.

Example:

``` text
Start: 2026-08-25 22:00
End:   2026-08-26 07:00
```

Do not assume the OUT event has the same calendar date as the IN event.
