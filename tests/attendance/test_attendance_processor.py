"""Integration tests for AttendanceProcessor — uses in-memory SQLite.

Tests 9–17 per the approved test matrix.
All tests share a single session-scoped in-memory DB, with per-test
data isolation via explicit setup.

Status priority order (canonical, documented in calculation_service.py):
    HOLIDAY > REST_DAY > ON_LEAVE > INCOMPLETE > HALF_DAY
    > LATE > UNDERTIME > OVERTIME > PRESENT
"""
from __future__ import annotations

import datetime as dt
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Force in-memory DB for all tests
os.environ["BIOMETRIC_DB_URL"] = "sqlite:///:memory:"

from biometric_attendance.infrastructure.data.models import Base
from biometric_attendance.infrastructure.data.models import (
    EmployeeModel,
    ShiftTemplateModel,
    HolidayModel,
    EmployeeScheduleModel,
)
from biometric_attendance.core.enums.scheduling import HolidayType, ScheduleStatus
from biometric_attendance.infrastructure.repositories.attendance_repository import (
    AttendanceEventRepository,
    AttendanceRecordRepository,
)
from biometric_attendance.infrastructure.repositories.scheduling_repository import (
    EmployeeScheduleRepository,
    ShiftTemplateRepository,
    HolidayRepository,
)
from biometric_attendance.infrastructure.repositories.workforce_repository import EmployeeRepository
from biometric_attendance.application.attendance.schedule_resolver import ScheduleResolver
from biometric_attendance.application.attendance.calculation_service import AttendanceCalculationService
from biometric_attendance.application.attendance.attendance_processor import AttendanceProcessor
from biometric_attendance.application.attendance.event_service import AttendanceEventService
from biometric_attendance.core.enums.attendance import AttendanceEventType, AttendanceSource, AttendanceStatus
from tests.attendance.fixtures import TODAY, ts


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    """Per-test transaction rollback for isolation."""
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(bind=connection)
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def employee(session):
    """Seed one employee with a Regular Shift and schedule on TODAY."""
    emp = EmployeeModel(
        employee_id="EMP-001",
        first_name="Test",
        last_name="Employee",
        grace_period_mins=10,
        overtime_eligible=True,
        rest_day="Sunday",
    )
    session.add(emp)
    session.flush()

    shift = ShiftTemplateModel(
        name="Regular Shift",
        start_time=dt.time(8, 0),
        end_time=dt.time(17, 0),
        grace_period_mins=10,
        late_threshold_mins=0,
        early_out_threshold_mins=0,
        overtime_threshold_mins=30,
        is_overnight=False,
        is_active=True,
    )
    session.add(shift)
    session.flush()

    sched = EmployeeScheduleModel(
        employee_id=emp.id,
        shift_template_id=shift.id,
        date=TODAY,
        is_rest_day=False,
        schedule_status=ScheduleStatus.ACTIVE,
    )
    session.add(sched)
    session.flush()

    return emp, shift, sched


def _make_processor(session):
    event_repo = AttendanceEventRepository(session)
    record_repo = AttendanceRecordRepository(session)
    emp_repo = EmployeeRepository(session)
    sched_repo = EmployeeScheduleRepository(session)
    shift_repo = ShiftTemplateRepository(session)
    holiday_repo = HolidayRepository(session)
    resolver = ScheduleResolver(sched_repo, shift_repo, holiday_repo)
    calc = AttendanceCalculationService()
    processor = AttendanceProcessor(event_repo, record_repo, emp_repo, resolver, calc)
    event_svc = AttendanceEventService(event_repo, processor)
    return event_svc, record_repo


# ── Test 9: IN only → INCOMPLETE ─────────────────────────────────────────────

def test_missing_out_creates_incomplete(session, employee):
    emp, shift, sched = employee
    svc, record_repo = _make_processor(session)

    result = svc.record_event(
        employee_id=emp.id,
        event_type=AttendanceEventType.IN,
        timestamp=ts(TODAY, 8, 5),
        source=AttendanceSource.MOCK,
    )
    assert result.record.status == AttendanceStatus.INCOMPLETE
    assert result.record.time_in is not None
    assert result.record.time_out is None


# ── Test 10: OUT only (missing IN) → INCOMPLETE ───────────────────────────────

def test_missing_in_creates_incomplete(session, employee):
    emp, shift, sched = employee
    svc, record_repo = _make_processor(session)

    result = svc.record_event(
        employee_id=emp.id,
        event_type=AttendanceEventType.OUT,
        timestamp=ts(TODAY, 17, 0),
        source=AttendanceSource.MOCK,
    )
    assert result.record.status == AttendanceStatus.INCOMPLETE
    assert result.record.time_in is None
    assert result.record.time_out is not None


# ── Test 11: Rest day scan → REST_DAY ────────────────────────────────────────

def test_rest_day_scan(session, employee):
    emp, shift, sched = employee
    svc, _ = _make_processor(session)

    # Modify schedule to be a rest day
    sched.is_rest_day = True
    session.flush()

    result = svc.record_event(
        employee_id=emp.id,
        event_type=AttendanceEventType.IN,
        timestamp=ts(TODAY, 8, 0),
        source=AttendanceSource.MOCK,
    )
    assert result.record.status == AttendanceStatus.REST_DAY


# ── Test 12: Holiday scan → HOLIDAY ──────────────────────────────────────────

def test_holiday_scan(session, employee):
    emp, shift, sched = employee
    svc, _ = _make_processor(session)

    holiday = HolidayModel(
        name="Test Holiday",
        date=TODAY,
        holiday_type=HolidayType.REGULAR,
        is_paid=True,
    )
    session.add(holiday)
    session.flush()

    result = svc.record_event(
        employee_id=emp.id,
        event_type=AttendanceEventType.IN,
        timestamp=ts(TODAY, 8, 0),
        source=AttendanceSource.MOCK,
    )
    assert result.record.status == AttendanceStatus.HOLIDAY


# ── Test 13: Leave stub → always False, does not block ───────────────────────

def test_leave_stub_returns_false(session, employee):
    """Phase 6 stub always returns False — leave check does not block the processor."""
    emp, shift, sched = employee
    svc, _ = _make_processor(session)

    # Processor's _has_approved_leave always returns False — should not mark ON_LEAVE
    result = svc.record_event(
        employee_id=emp.id,
        event_type=AttendanceEventType.IN,
        timestamp=ts(TODAY, 8, 0),
        source=AttendanceSource.MOCK,
    )
    # Should be INCOMPLETE (no OUT yet), not ON_LEAVE
    assert result.record.status != AttendanceStatus.ON_LEAVE
    assert result.record.status == AttendanceStatus.INCOMPLETE


# ── Test 14: Duplicate scan within 60s → deduplicated ────────────────────────

def test_duplicate_scan_within_60s(session, employee):
    emp, shift, sched = employee
    svc, _ = _make_processor(session)

    ts1 = ts(TODAY, 8, 0)
    ts2 = ts(TODAY, 8, 0).replace(second=30)  # 30 seconds later

    result1 = svc.record_event(
        employee_id=emp.id, event_type=AttendanceEventType.IN,
        timestamp=ts1, source=AttendanceSource.MOCK,
    )
    result2 = svc.record_event(
        employee_id=emp.id, event_type=AttendanceEventType.IN,
        timestamp=ts2, source=AttendanceSource.MOCK,
    )

    assert not result1.is_duplicate
    assert result2.is_duplicate
    assert "Duplicate scan ignored" in result2.message
    # Single record created, not two
    assert result1.record.id == result2.record.id


# ── Test 15: Full scan sequence IN/BREAK_OUT/BREAK_IN/OUT ────────────────────

def test_full_scan_sequence(session, employee):
    emp, shift, sched = employee
    svc, record_repo = _make_processor(session)

    svc.record_event(emp.id, AttendanceEventType.IN, ts(TODAY, 8, 0), source=AttendanceSource.MOCK)
    svc.record_event(emp.id, AttendanceEventType.BREAK_OUT, ts(TODAY, 12, 0), source=AttendanceSource.MOCK)
    svc.record_event(emp.id, AttendanceEventType.BREAK_IN, ts(TODAY, 13, 0), source=AttendanceSource.MOCK)
    result = svc.record_event(emp.id, AttendanceEventType.OUT, ts(TODAY, 17, 0), source=AttendanceSource.MOCK)

    rec = result.record
    assert rec.time_in is not None
    assert rec.break_out is not None
    assert rec.break_in is not None
    assert rec.time_out is not None
    # 9h gross - 1h break = 8h = 480 min
    assert rec.worked_minutes == 480
    assert rec.status == AttendanceStatus.PRESENT


# ── Test 16: Overnight shift — single record, correct worked minutes ──────────

def test_overnight_shift_single_record(session):
    """
    Overnight shift: IN at 22:00 on Aug 28, OUT at 07:00 on Aug 29.
    Expected: single AttendanceRecord dated Aug 28 (IN date per Q2).
    Worked minutes = 9 * 60 = 540.
    """
    with Session(bind=session.bind) as s:
        emp = EmployeeModel(
            employee_id="EMP-NIGHT",
            first_name="Night",
            last_name="Worker",
            grace_period_mins=10,
            overtime_eligible=False,
            rest_day="Sunday",
        )
        s.add(emp)
        s.flush()

        shift = ShiftTemplateModel(
            name="Night Shift",
            start_time=dt.time(22, 0),
            end_time=dt.time(7, 0),
            grace_period_mins=10,
            late_threshold_mins=0,
            early_out_threshold_mins=0,
            overtime_threshold_mins=30,
            is_overnight=True,
            is_active=True,
        )
        s.add(shift)
        s.flush()

        night_date = dt.date(2026, 8, 28)
        sched = EmployeeScheduleModel(
            employee_id=emp.id,
            shift_template_id=shift.id,
            date=night_date,
            is_rest_day=False,
            schedule_status=ScheduleStatus.ACTIVE,
        )
        s.add(sched)
        s.flush()

        svc, record_repo = _make_processor(s)

        # IN on Aug 28
        svc.record_event(
            emp.id, AttendanceEventType.IN,
            dt.datetime(2026, 8, 28, 22, 0),
            source=AttendanceSource.MOCK,
        )
        # OUT on Aug 29 — should attach to Aug 28 record
        result = svc.record_event(
            emp.id, AttendanceEventType.OUT,
            dt.datetime(2026, 8, 29, 7, 0),
            source=AttendanceSource.MOCK,
        )

        rec = result.record
        # Must be a single record with date = Aug 28 (IN date)
        assert rec.date == night_date, f"Expected {night_date}, got {rec.date}"
        assert rec.worked_minutes == 9 * 60, f"Expected 540, got {rec.worked_minutes}"
        # Not a new record (OUT was merged into existing IN record)
        assert not result.is_new_record


# ── Test 17: Offline sync — event timestamped 2h in the past ─────────────────

def test_offline_event_sync(session, employee):
    """An event with a past timestamp (simulating offline sync) is processed
    correctly based on the event's timestamp, not the current wall clock."""
    emp, shift, sched = employee
    svc, _ = _make_processor(session)

    two_hours_ago = ts(TODAY, 8, 0)  # Simulated "past" timestamp
    result = svc.record_event(
        employee_id=emp.id,
        event_type=AttendanceEventType.IN,
        timestamp=two_hours_ago,
        source=AttendanceSource.MOCK,
    )
    assert result.record.time_in == two_hours_ago
    assert result.record.status == AttendanceStatus.INCOMPLETE
