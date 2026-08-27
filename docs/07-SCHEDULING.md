# Scheduling Module

## 1. Goal

Define when employees are expected to work and provide the rules used by
the attendance engine.

## 2. Shift Template

Fields:

-   Shift Name
-   Start Time
-   End Time
-   Break Start
-   Break End
-   Grace Period
-   Late Threshold
-   Early Out Threshold
-   Overtime Threshold

Example:

``` text
Regular Shift
08:00 AM – 05:00 PM
Grace: 10 minutes
```

## 3. Employee Schedule

Fields:

-   Employee
-   Shift
-   Date
-   Start
-   End
-   Rest Day
-   Schedule Status

## 4. Calendar UI

Provide:

-   Monthly calendar
-   Weekly view
-   Employee filter
-   Department filter
-   Drag/drop assignment if practical
-   Bulk assignment

## 5. Bulk Scheduling

Example:

``` text
Employees:
IT Department

Shift:
Regular

Date Range:
Aug 25 – Aug 31

Action:
Assign
```

## 6. Holidays

Holiday fields:

-   Name
-   Date
-   Type
-   Paid
-   Notes

Types:

-   Regular Holiday
-   Special Non-Working Holiday
-   Company Holiday

## 7. Rest Days

Rest days must be represented independently from absence.

A scheduled rest day should not become an ABSENT record.

## 8. Overnight Scheduling

Support shifts crossing midnight using DateTime schedule instances.
