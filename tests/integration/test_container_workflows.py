"""Regression checks using production DI wiring and isolated SQLite storage."""
import datetime as dt

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from biometric_attendance.app.container import AppContainer
from biometric_attendance.core.enums.attendance import AttendanceEventType, CorrectionType
from biometric_attendance.core.enums.biometrics import FingerType
from biometric_attendance.core.enums.workforce import EmploymentStatus
from biometric_attendance.infrastructure.adapters.mock_biometric_adapter import MockBiometricAdapter
from biometric_attendance.infrastructure.data import database
from biometric_attendance.infrastructure.data.models import (
    Base, EmployeeModel, EmployeeScheduleModel, ShiftTemplateModel, UserModel,
)

DAY = dt.date(2026, 9, 1)


@pytest.fixture
def app(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    monkeypatch.setattr(database, "SessionFactory", factory)
    monkeypatch.setenv("BIOMETRIC_ENCRYPTION_KEY", Fernet.generate_key().decode())
    with factory.begin() as session:
        employee = EmployeeModel(employee_id="TEST-1", first_name="Test", last_name="Employee")
        session.add(employee)
        session.flush()
        employee_id = employee.id
    yield AppContainer(), factory, employee_id
    engine.dispose()


def scan(container, employee_id, day, hour, event_type=AttendanceEventType.IN):
    return container.attendance_event_service().record_event(
        employee_id, event_type, dt.datetime.combine(day, dt.time(hour)),
    )


def test_container_attendance_and_correction_repositories(app):
    container, factory, employee_id = app
    result = scan(container, employee_id, DAY, 8)
    assert len(container.attendance_event_repository().get_by_employee_and_date(employee_id, DAY)) == 1
    assert len(container.attendance_event_repository().get_by_date_range(DAY, DAY)) == 1
    assert len(container.attendance_record_repository().get_by_date_range(DAY, DAY)) == 1
    assert container.attendance_record_repository().get_by_employee_and_date(employee_id, DAY).id == result.record.id
    with factory.begin() as session:
        user = UserModel(username="reviewer", display_name="Reviewer", email="test@example.com", hashed_password="unused")
        session.add(user)
        session.flush()
        user_id = user.id
    correction = container.attendance_correction_service().submit_correction(
        result.record.id, employee_id, CorrectionType.TIME_OUT, "", "2026-09-01T17:00:00", "Missed scan", user_id,
    )
    repo = container.attendance_correction_repository()
    assert repo.get_pending()[0].id == correction.id
    assert repo.get_by_record(result.record.id)[0].id == correction.id
    assert repo.get_by_employee(employee_id)[0].id == correction.id
    container.attendance_correction_service().reject_correction(correction.id, user_id, "Declined")
    assert repo.get_pending() == []


@pytest.mark.parametrize("event_type", [AttendanceEventType.IN, AttendanceEventType.OUT])
def test_day_shift_missing_out_does_not_take_next_days_scan(app, event_type):
    container, factory, employee_id = app
    original = scan(container, employee_id, DAY, 8)
    result = scan(container, employee_id, DAY + dt.timedelta(days=1), 8, event_type)
    assert result.record.date == DAY + dt.timedelta(days=1)
    assert result.record.id != original.record.id


def test_historical_scan_is_not_duplicate_of_later_day(app):
    container, _, employee_id = app
    scan(container, employee_id, DAY, 8)
    earlier_day = DAY - dt.timedelta(days=14)
    result = scan(container, employee_id, earlier_day, 8)
    assert not result.is_duplicate
    assert result.record.date == earlier_day


def test_out_of_order_scans_within_window_are_duplicates(app):
    container, _, employee_id = app
    scan(container, employee_id, DAY, 8)
    result = container.attendance_event_service().record_event(
        employee_id, AttendanceEventType.IN, dt.datetime(2026, 9, 1, 7, 59, 30),
    )
    assert result.is_duplicate


@pytest.mark.parametrize("event_type", [AttendanceEventType.IN, AttendanceEventType.OUT, AttendanceEventType.BREAK_OUT])
def test_overnight_routing_with_consecutive_schedules(app, event_type):
    container, factory, employee_id = app
    next_day = DAY + dt.timedelta(days=1)
    with factory.begin() as session:
        shift = ShiftTemplateModel(name="Night", start_time=dt.time(22), end_time=dt.time(7), is_overnight=True)
        session.add(shift)
        session.flush()
        for day in (DAY, next_day):
            session.add(EmployeeScheduleModel(employee_id=employee_id, shift_template_id=shift.id, date=day))
    original = scan(container, employee_id, DAY, 22)
    result = scan(container, employee_id, next_day, 7 if event_type != AttendanceEventType.IN else 22, event_type)
    if event_type == AttendanceEventType.IN:
        assert result.record.date == next_day
        assert result.record.id != original.record.id
        # An old unclosed shift must not steal this new shift's OUT either.
        out = scan(container, employee_id, next_day, 23, AttendanceEventType.OUT)
        assert out.record.id == result.record.id
    else:
        assert result.record.date == DAY
        assert result.record.id == original.record.id
        if event_type == AttendanceEventType.OUT:
            assert result.record.worked_minutes == 540


def test_biometric_connection_pull_and_push(app, monkeypatch):
    container, factory, employee_id = app
    with factory.begin() as session:
        archived = EmployeeModel(employee_id="ARCHIVED", first_name="Old", last_name="Employee", status=EmploymentStatus.ARCHIVED)
        session.add(archived)
        session.flush()
        archived_id = archived.id
    device = container.biometric_device_service().register_device("Mock", "127.0.0.1", 4370)
    assert container.biometric_device_service().test_connection(device.id)
    pulled = container.biometric_sync_service().pull_logs(device.id)
    assert 1 <= pulled <= 4
    events = container.attendance_event_repository().get_by_date_range(dt.date.today(), dt.date.today())
    assert len(events) == pulled
    assert {e.employee_id for e in events} == {employee_id}
    for emp_id in (employee_id, archived_id):
        container.biometric_enrollment_service().enroll_fingerprint(emp_id, FingerType.LEFT_THUMB, container.mock_adapter_factory([]))
    pushed = []
    monkeypatch.setattr(MockBiometricAdapter, "push_user", lambda self, emp, template: pushed.append((emp, template)))
    assert container.biometric_sync_service().push_users(device.id) == 1
    assert pushed[0][0] == "TEST-1"
    assert pushed[0][1].startswith(b"MOCK_TEMPLATE_")
