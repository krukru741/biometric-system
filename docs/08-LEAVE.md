# Leave Management

## 1. Goal

Manage leave requests, approvals, balances, and attendance integration.

## 2. Leave Types

Examples:

-   Vacation Leave
-   Sick Leave
-   Emergency Leave
-   Maternity Leave
-   Paternity Leave
-   Service Incentive Leave
-   Company-defined leave types

## 3. Employee Request UI

Fields:

-   Leave Type
-   Start Date
-   End Date
-   Reason
-   Number of Days
-   Attachment if required

Flow:

``` text
Draft
  ↓
Submitted
  ↓
Pending Approval
  ↓
Approved / Rejected
```

## 4. Approval UI

Show:

-   Employee
-   Leave type
-   Dates
-   Number of days
-   Reason
-   Attachment
-   Current leave balance
-   Approve
-   Reject

## 5. Attendance Integration

Approved leave should affect attendance processing:

``` text
Schedule
+
Approved Leave
=
ON_LEAVE
```

Do not mark an approved leave as ABSENT.

## 6. Database Entities

``` text
LeaveType
LeaveRequest
LeaveBalance
```

## 7. Audit

Record:

-   Who submitted
-   Who approved/rejected
-   When
-   Previous status
-   New status
-   Reason
