# Security and Audit

## 1. Security Objectives

Protect:

-   Employee personal information
-   Attendance history
-   Biometric templates
-   User credentials
-   Administrative actions

## 2. Authentication

-   Strong password hashing
-   Account status checking
-   Session timeout
-   Login failure handling
-   Password reset process

## 3. Authorization

Authorization must be enforced at the application/service layer.

Do not rely only on hiding buttons.

## 4. Biometric Protection

-   Encrypt biometric templates
-   Restrict access
-   Never expose templates in normal UI
-   Log enrollment/deletion/replacement
-   Follow applicable privacy and organizational policies

## 5. Audit Events

Log:

-   Login
-   Logout
-   Failed login
-   Employee creation
-   Employee modification
-   Biometric enrollment
-   Biometric deletion
-   Attendance correction
-   Leave approval/rejection
-   Overtime approval/rejection
-   User role changes
-   System settings changes
-   Database restore

## 6. Audit Record

``` text
AuditLog
----------------
Id
UserId
Action
Module
EntityName
EntityId
OldValue
NewValue
Timestamp
MachineName
```

## 7. Principle

Attendance corrections and biometric changes should always be traceable.
