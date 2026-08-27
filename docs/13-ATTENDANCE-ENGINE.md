# Attendance Processing Engine

## 1. Purpose

The Attendance Engine is the business-logic layer that converts
biometric events and schedules into attendance results.

## 2. Inputs

-   Employee
-   Attendance events
-   Employee schedule
-   Shift rules
-   Grace period
-   Holidays
-   Rest days
-   Approved leave
-   Approved overtime
-   System settings

## 3. Processing Flow

``` text
Event
 ↓
Identify Employee
 ↓
Find Schedule
 ↓
Check Holiday
 ↓
Check Rest Day
 ↓
Check Approved Leave
 ↓
Classify Event
 ↓
Build Attendance Record
 ↓
Calculate:
  Late
  Worked Minutes
  Undertime
  Overtime
 ↓
Assign Status
 ↓
Save
 ↓
Audit
```

## 4. Example

Shift:

``` text
08:00 – 17:00
Grace: 10 minutes
```

Scan:

``` text
08:07
```

Result:

``` text
TimeIn = 08:07
Late = 0
Status = PRESENT
```

Scan:

``` text
08:15
```

Result:

``` text
TimeIn = 08:15
Late = 15
Status = LATE
```

## 5. Incomplete Attendance

If an employee has IN but no OUT:

``` text
Status = INCOMPLETE
```

Do not automatically invent a TimeOut.

## 6. Overnight Shift

Use schedule DateTime boundaries rather than only TimeSpan.

Example:

``` text
Start = 2026-08-25 22:00
End   = 2026-08-26 07:00
```

## 7. Service Design

Suggested services (defined as Python abstract base classes / Protocols):

``` python
class IAttendanceProcessor(ABC): ...
class IAttendanceCalculationService(ABC): ...
class IScheduleResolver(ABC): ...
class IAttendanceEventService(ABC): ...
class IAttendanceCorrectionService(ABC): ...
```

## 8. Test Cases

Must test:

-   On-time
-   Within grace
-   Late
-   Missing IN
-   Missing OUT
-   Rest day
-   Holiday
-   Approved leave
-   Half day
-   Undertime
-   Overtime
-   Overnight shift
-   Duplicate scan
-   Offline event sync
-   Multiple scans within seconds
