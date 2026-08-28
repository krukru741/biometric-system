"""Unit tests for AttendanceCalculationService — pure math, no DB.

Tests 1-7 per the approved test matrix.
All tests use the canonical status priority order:
    HOLIDAY > REST_DAY > ON_LEAVE > INCOMPLETE > HALF_DAY
    > LATE > UNDERTIME > OVERTIME > PRESENT
"""
from __future__ import annotations

import datetime as dt

import pytest

from biometric_attendance.application.attendance.calculation_service import (
    AttendanceCalculationService,
)
from biometric_attendance.core.enums.attendance import AttendanceStatus
from tests.attendance.fixtures import (
    TODAY,
    make_shift,
    ts,
)

svc = AttendanceCalculationService()


# ── Test 1: On-time (time_in before grace window) ────────────────────────────

def test_on_time_within_grace():
    """08:05 arrival, 10-min grace → late_minutes = 0, status = PRESENT."""
    shift = make_shift(grace_period_mins=10)
    result = svc.calculate(
        time_in=ts(TODAY, 8, 5),
        time_out=ts(TODAY, 17, 0),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    assert result.late_minutes == 0
    assert result.status == AttendanceStatus.PRESENT
    assert result.worked_minutes > 0


# ── Test 2: Exactly at grace boundary ─────────────────────────────────────────

def test_within_grace_boundary():
    """08:10 arrival, 10-min grace → late_minutes = 0 (within grace)."""
    shift = make_shift(grace_period_mins=10)
    result = svc.calculate(
        time_in=ts(TODAY, 8, 10),
        time_out=ts(TODAY, 17, 0),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    assert result.late_minutes == 0
    assert result.status == AttendanceStatus.PRESENT


# ── Test 3: Late ──────────────────────────────────────────────────────────────

def test_late():
    """08:15 arrival, 10-min grace → late_minutes = 15."""
    shift = make_shift(grace_period_mins=10)
    result = svc.calculate(
        time_in=ts(TODAY, 8, 15),
        time_out=ts(TODAY, 17, 0),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    assert result.late_minutes == 15
    assert result.status == AttendanceStatus.LATE


# ── Test 4: Undertime ─────────────────────────────────────────────────────────

def test_undertime():
    """OUT at 16:00, shift ends 17:00, no early-out threshold → undertime = 60 min."""
    shift = make_shift(early_out_threshold_mins=0)
    result = svc.calculate(
        time_in=ts(TODAY, 8, 0),
        time_out=ts(TODAY, 16, 0),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    assert result.undertime_minutes == 60
    assert result.status == AttendanceStatus.UNDERTIME


# ── Test 5: Overtime ──────────────────────────────────────────────────────────

def test_overtime():
    """OUT at 18:30, OT threshold 30 min → overtime = 60 min."""
    shift = make_shift(overtime_threshold_mins=30)
    result = svc.calculate(
        time_in=ts(TODAY, 8, 0),
        time_out=ts(TODAY, 18, 30),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    assert result.overtime_minutes > 0
    assert result.status == AttendanceStatus.OVERTIME


def test_overtime_not_eligible():
    """Overtime NOT awarded when employee is not overtime_eligible."""
    shift = make_shift(overtime_threshold_mins=30)
    result = svc.calculate(
        time_in=ts(TODAY, 8, 0),
        time_out=ts(TODAY, 18, 30),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=False,
    )
    assert result.overtime_minutes == 0
    # Should be PRESENT since no undertime, no late, no overtime
    assert result.status == AttendanceStatus.PRESENT


# ── Test 6: Break duration deducted from worked minutes ──────────────────────

def test_break_deducted_from_worked_minutes():
    """1-hour break (12:00–13:00) → worked minutes = 8h, not 9h gross."""
    shift = make_shift(break_start=dt.time(12, 0), break_end=dt.time(13, 0))
    result = svc.calculate(
        time_in=ts(TODAY, 8, 0),
        time_out=ts(TODAY, 17, 0),
        break_out=ts(TODAY, 12, 0),
        break_in=ts(TODAY, 13, 0),
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    # gross = 9h = 540 min; break = 60 min; worked = 480 min
    assert result.worked_minutes == 480


# ── Test 7: Overnight shift — worked minutes span midnight ───────────────────

def test_overnight_worked_minutes():
    """22:00 IN, 07:00 next day OUT — worked minutes = 9 * 60 = 540."""
    overnight_date = dt.date(2026, 8, 28)
    shift = make_shift(
        start_time=dt.time(22, 0),
        end_time=dt.time(7, 0),
        is_overnight=True,
        overtime_threshold_mins=30,
    )
    result = svc.calculate(
        time_in=dt.datetime(2026, 8, 28, 22, 0),
        time_out=dt.datetime(2026, 8, 29, 7, 0),
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=overnight_date,
        overtime_eligible=True,
    )
    assert result.worked_minutes == 9 * 60


# ── Test 8: Half-day (< 50% of shift) ────────────────────────────────────────

def test_half_day():
    """Worked only 4h out of 9h expected (< 50%) → HALF_DAY."""
    shift = make_shift()
    result = svc.calculate(
        time_in=ts(TODAY, 8, 0),
        time_out=ts(TODAY, 12, 0),   # 4 hours
        break_out=None,
        break_in=None,
        shift=shift,
        schedule_date=TODAY,
        overtime_eligible=True,
    )
    # Expected = 9 * 60 = 540. Half = 270. Worked = 4 * 60 = 240 < 270 → HALF_DAY
    assert result.status == AttendanceStatus.HALF_DAY
