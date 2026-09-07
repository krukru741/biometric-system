"""Headless Qt behavior checks; no real database or scanner is used."""
import datetime as dt
import os
import threading
import time
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton

from biometric_attendance.app.viewmodels.async_loader import AsyncLoader
from biometric_attendance.app.viewmodels.attendance_vms import AttendanceRecordsViewModel
from biometric_attendance.app.widgets.components import Column, ContentState, FilterBar, RecordTable
from biometric_attendance.app.views.attendance.attendance_records_view import AttendanceRecordsView


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def until(predicate, timeout=3000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    assert predicate(), "Timed out waiting for Qt result"


def test_model_sort_missing_values_and_selection(qapp):
    table = RecordTable([Column("Minutes", lambda r: r.minutes)], name="Hours", row_key=lambda r: r.id)
    rows = [SimpleNamespace(id=1, minutes=100), SimpleNamespace(id=2, minutes=9), SimpleNamespace(id=3, minutes=None)]
    table.set_rows(rows)
    table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
    assert [table.model().index(i, 0).data() for i in range(3)] == ["—", "9", "100"]
    table.setCurrentIndex(table.model().index(1, 0))
    table.set_rows(list(reversed(rows)))
    assert table.selected_record().id == 2
    table.set_rows([])
    assert table.selected_record() is None
    assert table.accessibleName() == "Hours"
    table.deleteLater()


def test_state_retry_keyboard_and_plain_text(qapp):
    state = ContentState(QLineEdit())
    state.resize(600, 300)
    state.show()
    state.show_state("error", "<b>Failure</b>", "Try again", action="Retry")
    assert state.title.textFormat() == Qt.TextFormat.PlainText
    assert not state.progress.isVisible()
    called = []
    state.action_requested.connect(lambda: called.append(True))
    state.action.setFocus()
    QTest.keyClick(state.action, Qt.Key.Key_Space)
    assert called == [True]
    state.show_state("loading", "Loading")
    assert state.progress.isVisible()
    assert not state.action.isVisible()
    state.show_content()
    assert state.content.isVisible()
    with pytest.raises(ValueError):
        state.show_state("unknown", "")
    state.close()
    state.deleteLater()


def test_filters_wrap_and_expose_accessible_labels(qapp):
    filters = FilterBar()
    controls = [QLineEdit() for _ in range(4)]
    for i, control in enumerate(controls):
        filters.add_field(f"Field {i}", control)
    filters.resize(1000, 300)
    filters.show()
    qapp.processEvents()
    assert filters._columns == 4
    filters.resize(400, 400)
    qapp.processEvents()
    assert filters._columns == 1
    assert controls[0].accessibleName() == "Field 0"
    assert controls[-1].mapTo(filters, controls[-1].rect().topLeft()).y() > controls[0].mapTo(filters, controls[0].rect().topLeft()).y()
    filters.close()
    filters.deleteLater()


def test_async_loader_coalesces_and_delivers_on_gui_thread(qapp):
    loader = AsyncLoader()
    gate = threading.Event()
    received, executed, threads = [], [], []
    loader.loaded.connect(lambda value: (received.append(value), threads.append(QThread.currentThread())))
    def first():
        assert gate.wait(2)
        return "stale"
    loader.load(first)
    loader.load(lambda: executed.append("skipped"))
    loader.load(lambda: "latest")
    # UI event loop remains responsive while the worker is blocked.
    qapp.processEvents()
    gate.set()
    until(lambda: bool(received))
    assert received == ["latest"]
    assert executed == []
    assert threads == [qapp.thread()]
    loader.deleteLater()


def test_async_error_is_safe_and_retry_recovers(qapp):
    loader = AsyncLoader(error_message="Please retry")
    failures, received = [], []
    loader.failed.connect(failures.append)
    loader.loaded.connect(received.append)
    loader.load(lambda: (_ for _ in ()).throw(RuntimeError("private database path")))
    until(lambda: bool(failures))
    assert failures == ["Please retry"]
    loader.load(lambda: "ready")
    until(lambda: bool(received))
    assert received == ["ready"]
    loader.deleteLater()


def test_attendance_loader_bounds_query_and_pages(qapp):
    calls = []
    class Repo:
        def get_by_date_range(self, **kwargs):
            calls.append((kwargs, QThread.currentThread()))
            return list(range(101))
    vm = AttendanceRecordsViewModel(Repo(), None)
    rows, pages = [], []
    vm.records_loaded.connect(rows.append)
    vm.page_loaded.connect(lambda page, more: pages.append((page, more)))
    vm.load_records(dt.date(2026, 1, 1), dt.date(2026, 2, 1), page=2)
    until(lambda: bool(rows))
    assert len(rows[0]) == 100
    assert pages == [(2, True)]
    assert calls[0][0]["limit"] == 101 and calls[0][0]["offset"] == 200
    assert calls[0][1] != qapp.thread()
    vm.deleteLater()


class FakeRecordsVM(QObject):
    employees_loaded = Signal(list)
    records_loaded = Signal(list)
    page_loaded = Signal(int, bool)
    loading_changed = Signal(bool)
    absent_generated = Signal(int)
    error_occurred = Signal(str)
    def __init__(self):
        super().__init__()
        self.calls = []
    def load_employees(self):
        self.employees_loaded.emit([])
    def load_records(self, **kwargs):
        self.calls.append(kwargs)
        self.loading_changed.emit(True)
    def generate_absent_records(self, date):
        pass


def test_attendance_view_loading_empty_error_validation(qapp):
    vm = FakeRecordsVM()
    view = AttendanceRecordsView(vm)
    view.resize(640, 800)
    view.show()
    qapp.processEvents()
    assert view.content_state.state == "loading"
    assert not view.fetch_btn.isEnabled()
    vm.loading_changed.emit(False)
    vm.page_loaded.emit(0, False)
    vm.records_loaded.emit([])
    assert view.content_state.state == "empty"
    assert not view.next_btn.isEnabled()
    vm.error_occurred.emit("Try again")
    assert view.content_state.state == "error"
    QTest.qWait(50)
    assert view.content_state.title.height() >= 36
    for control in (view.start_date, view.end_date, view.emp_combo, view.fetch_btn):
        assert control.height() >= 36
    view.start_date.setDate(view.end_date.date().addDays(1))
    count = len(vm.calls)
    view._apply_filters()
    assert len(vm.calls) == count
    assert view.validation.isVisible()
    view.close()
    view.deleteLater()


def test_employee_view_search_selection_and_archived_actions(qapp):
    from dataclasses import replace
    from biometric_attendance.app.viewmodels.workforce_vms import EmployeesViewModel
    from biometric_attendance.app.views.workforce.employees_view import EmployeesView
    from biometric_attendance.core.enums.workforce import EmploymentStatus
    from tests.attendance.fixtures import make_employee
    active = make_employee()
    archived = replace(active, id=2, employee_id="ARCHIVED", status=EmploymentStatus.ARCHIVED)
    class Service:
        def get_all_departments(self): return []
        def get_all_positions(self): return []
        def get_all_employees(self): return [active, archived]
    vm = EmployeesViewModel(Service())
    view = EmployeesView(vm)
    view.resize(900, 800)
    view.show()
    until(lambda: view.content_state.state == "content")
    assert view.table.model().rowCount() == 1
    view.table.setCurrentIndex(view.table.model().index(0, 0))
    assert view.view_btn.isEnabled() and view.archive_btn.isEnabled()
    assert active.full_name in view.view_btn.accessibleName()
    view.status_filter.setCurrentIndex(2)
    view.table.setCurrentIndex(view.table.model().index(0, 0))
    assert view.view_btn.isEnabled() and not view.archive_btn.isEnabled()
    view.search_input.setText("no match")
    until(lambda: view.content_state.state == "empty")
    assert not view.view_btn.isEnabled()
    view.close()
    view.deleteLater()


def test_loader_can_be_destroyed_during_read(qapp):
    import shiboken6
    from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool
    loader = AsyncLoader()
    gate = threading.Event()
    delivered = []
    loader.loaded.connect(delivered.append)
    loader.load(lambda: gate.wait(2))
    loader.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not shiboken6.isValid(loader)
    gate.set()
    until(lambda: QThreadPool.globalInstance().activeThreadCount() == 0)
    qapp.processEvents()
    assert delivered == []
