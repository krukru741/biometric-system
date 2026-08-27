# Administration

## 1. User Management

Fields:

-   Username
-   Display Name
-   Email
-   Password status
-   Account status
-   Roles
-   Last Login

Actions:

-   Create
-   Edit
-   Disable
-   Reset Password
-   Assign Role

## 2. Roles

Use role-permission relationships.

``` text
User
  ↓
UserRole
  ↓
Role
  ↓
RolePermission
  ↓
Permission
```

## 3. System Settings

### General

-   Company name
-   Company logo
-   Address
-   Contact information

### Attendance

-   Grace period
-   Late rules
-   Undertime rules
-   Overtime rules
-   Break rules
-   IN/OUT detection

### Biometrics

-   Device settings
-   Default scanner
-   Sync interval
-   Template configuration

## 4. Database

Provide:

-   Connection status
-   Backup
-   Restore
-   Database information
-   Last backup
-   Backup schedule

## 5. Backup UX

``` text
Last Backup:
2026-08-25 02:00 AM

Status:
Successful

[ Backup Now ]
[ Restore ]
```

## 6. Audit Logs

Record:

-   User
-   Action
-   Module
-   Entity
-   Entity ID
-   Old Value
-   New Value
-   Timestamp
-   IP / machine information where appropriate

## 7. Security

Administrative functions must require appropriate permissions and should
be logged.
