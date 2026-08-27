# Offline Mode and Device Synchronization

## 1. Goal

Attendance capture should remain operational even if the central
database or network temporarily becomes unavailable.

## 2. Offline Architecture

``` text
Biometric Scanner
      ↓
Local Application
      ↓
Local Queue
      ↓
Central Database
```

## 3. Local Queue

Store pending events locally with:

-   Local ID
-   Employee ID
-   Device ID
-   Event type
-   Timestamp
-   Verification result
-   Sync status
-   Retry count
-   Error message

## 4. Synchronization

``` text
Connection Available?
      │
     Yes
      ↓
Read Pending Events
      ↓
Validate
      ↓
Upload
      ↓
Mark Synced
```

## 5. Failure Handling

If upload fails:

-   Keep event locally
-   Increase retry count
-   Store error
-   Retry later
-   Never silently discard the event

## 6. Device Dashboard

Display:

-   Online/offline
-   Last connection
-   Last sync
-   Pending events
-   Failed events
-   Device model
-   IP address

## 7. Duplicate Prevention

Use a device-provided event ID when available.

If not available, use a carefully designed idempotency key based on
device, employee, event timestamp, and event sequence where appropriate.

## 8. Conflict Handling

If the same attendance event exists in both local and central storage:

``` text
Detect duplicate
  ↓
Keep canonical event
  ↓
Mark duplicate
  ↓
Audit
```
