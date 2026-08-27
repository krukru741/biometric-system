# Overtime Module

## 1. Goal

Manage requested, approved, and calculated overtime.

## 2. Request

Fields:

-   Employee
-   Date
-   Start Time
-   End Time
-   Reason
-   Attachment if required

Example:

``` text
Scheduled:
08:00 AM – 05:00 PM

Requested OT:
05:00 PM – 07:00 PM
```

## 3. Approval Flow

``` text
Employee Request
  ↓
Supervisor / HR Review
  ↓
Approved / Rejected
  ↓
Attendance Processing
  ↓
Overtime Calculation
```

## 4. Overtime Rules

Possible configuration:

-   Minimum OT minutes
-   Rounding rule
-   Maximum daily OT
-   Approval required
-   Holiday OT multiplier
-   Rest-day OT rule

## 5. Attendance Integration

Only approved overtime should normally become official overtime, unless
system policy explicitly allows automatic OT.

## 6. Database Entity

``` text
OvertimeRequest
--------------------
Id
EmployeeId
Date
StartTime
EndTime
RequestedMinutes
ApprovedMinutes
Reason
Status
ApprovedBy
ApprovedAt
CreatedAt
```
