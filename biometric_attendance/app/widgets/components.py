"""Reusable, domain-independent Qt page components. See docs/18-UI-COMPONENTS.md."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QSize, Qt, Signal
from PySide6.QtGui import QAccessible, QAccessibleEvent
from PySide6.QtWidgets import (
    QAbstractItemView, QBoxLayout, QGridLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QSizePolicy, QStackedWidget, QTableView,
    QVBoxLayout, QWidget,
)


def plain_label(text: str, parent: QWidget | None = None) -> QLabel:
    label = QLabel(text, parent)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


class PageHeader(QWidget):
    def __init__(self, title: str, description: str = "", *, action: QWidget | None = None, parent=None):
        super().__init__(parent)
        self._layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(16)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        text = QWidget()
        text_layout = QVBoxLayout(text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        self.title = plain_label(title)
        self.title.setObjectName("PageTitle")
        text_layout.addWidget(self.title)
        if description:
            text_layout.addWidget(plain_label(description))
        self._layout.addWidget(text, 1)
        self._text = text
        self._action = action
        if action is not None:
            action.setMinimumHeight(36)
            self._layout.addWidget(action)

    def heightForWidth(self, width):
        action_width = self._action.sizeHint().width() if self._action else 0
        text_width = width if width < 620 else max(1, width - action_width - 16)
        text_height = self._text.layout().totalHeightForWidth(text_width)
        text_height = max(text_height, self._text.minimumSizeHint().height())
        action_height = max(36, self._action.sizeHint().height()) if self._action else 0
        return text_height + action_height + 16 if width < 620 and self._action else max(text_height, action_height)

    def resizeEvent(self, event):
        self._layout.setDirection(
            QBoxLayout.Direction.TopToBottom if self.width() < 620 else QBoxLayout.Direction.LeftToRight
        )
        self.updateGeometry()
        super().resizeEvent(event)


class FilterBar(QWidget):
    """Fields wrap by available width, retaining creation/tab order."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self._fields: list[QWidget] = []
        self._columns = 0
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def heightForWidth(self, width):
        columns = max(1, min(len(self._fields), width // 220))
        heights = [max(field.minimumSizeHint().height(), field.sizeHint().height()) for field in self._fields]
        return sum(max(heights[i:i + columns]) for i in range(0, len(heights), columns)) + max(0, (len(heights) - 1) // columns) * 12

    def sizeHint(self):
        return QSize(900, self.heightForWidth(900))

    def add_field(self, label: str, control: QWidget) -> None:
        field = QWidget(self)
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        caption = plain_label(label)
        caption.setBuddy(control)
        control.setAccessibleName(label.replace("&", ""))
        control.setMinimumHeight(36)
        control.setMinimumWidth(0)
        control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(caption)
        layout.addWidget(control)
        self._fields.append(field)
        self._reflow()

    def add_action(self, action: QWidget) -> None:
        action.setMinimumHeight(36)
        self._fields.append(action)
        self._reflow()

    def _reflow(self):
        columns = max(1, min(len(self._fields), self.width() // 220))
        for column in range(max(self._columns, columns)):
            self._layout.setColumnStretch(column, 1 if column < columns else 0)
        for index, field in enumerate(self._fields):
            self._layout.addWidget(field, index // columns, index % columns, Qt.AlignmentFlag.AlignBottom)
        self._columns = columns
        self.updateGeometry()

    def resizeEvent(self, event):
        self._reflow()
        super().resizeEvent(event)


class ContentState(QWidget):
    """Owns content and explicit loading/empty/error states; action is a signal."""
    action_requested = Signal()

    def __init__(self, content: QWidget, parent=None):
        super().__init__(parent)
        self.state = "content"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        self.content = content
        self.stack.addWidget(content)
        self.message = QWidget()
        box = QVBoxLayout(self.message)
        box.setContentsMargins(24, 24, 24, 24)
        box.addStretch()
        self.title = plain_label("")
        self.title.setObjectName("SectionTitle")
        self.title.setMinimumHeight(36)
        self.title.setContentsMargins(4, 4, 4, 4)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.detail = plain_label("")
        self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Loading")
        self.action = QPushButton()
        self.action.setObjectName("SecondaryButton")
        self.action.setMinimumHeight(36)
        self.action.clicked.connect(self.action_requested)
        for widget in (self.title, self.detail, self.progress, self.action):
            box.addWidget(widget)
        box.addStretch()
        self.stack.addWidget(self.message)

    def show_content(self) -> None:
        had_focus = self.message.isAncestorOf(self.focusWidget()) if self.focusWidget() else False
        self.state = "content"
        self.stack.setCurrentWidget(self.content)
        self.setAccessibleDescription("Content loaded")
        if had_focus:
            self.content.setFocus()

    def show_state(self, state: str, title: str, detail: str = "", *, action: str = "") -> None:
        if state not in {"loading", "empty", "error"}:
            raise ValueError(f"Unknown content state: {state}")
        had_focus = self.content.hasFocus() or (self.focusWidget() and self.content.isAncestorOf(self.focusWidget()))
        self.state = state
        self.title.setText(title)
        self.title.setAccessibleName(title)
        self.detail.setText(detail)
        self.progress.setVisible(state == "loading")
        self.action.setText(action)
        self.action.setVisible(bool(action) and state != "loading")
        self.stack.setCurrentWidget(self.message)
        self.setAccessibleDescription(f"{title}. {detail}")
        QAccessible.updateAccessibility(QAccessibleEvent(self, QAccessible.Event.DescriptionChanged))
        if had_focus:
            self.title.setFocus()


@dataclass(frozen=True)
class Column:
    """Value feeds typed sorting; format is presentation only."""
    title: str
    value: Callable[[Any], Any]
    format: Callable[[Any], str] = str
    width: int = 130


class RecordModel(QAbstractTableModel):
    def __init__(self, columns: Sequence[Column], parent=None):
        super().__init__(parent)
        self.columns = tuple(columns)
        self.rows: tuple[Any, ...] = ()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.rows)):
            return None
        column = self.columns[index.column()]
        value = column.value(self.rows[index.row()])
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.AccessibleTextRole):
            return "—" if value is None else column.format(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.columns[section].title
        return super().headerData(section, orientation, role)

    def set_rows(self, rows: Sequence[Any]) -> None:
        self.beginResetModel()
        self.rows = tuple(rows)
        self.endResetModel()


class _TypedSort(QSortFilterProxyModel):
    def lessThan(self, left, right):
        model = self.sourceModel()
        column = model.columns[left.column()]
        a, b = (column.value(model.rows[i.row()]) for i in (left, right))
        if a is None or b is None:
            return a is None and b is not None
        if isinstance(a, str) and isinstance(b, str):
            return a.casefold() < b.casefold()
        try:
            return a < b
        except TypeError:
            return str(a).casefold() < str(b).casefold()


class RecordTable(QTableView):
    """Model-backed table: no widgets/items per cell; preserves selection by key."""
    def __init__(self, columns: Sequence[Column], *, name: str, row_key: Callable[[Any], Any], parent=None):
        super().__init__(parent)
        self.row_key = row_key
        self.records = RecordModel(columns, self)
        self.proxy = _TypedSort(self)
        self.proxy.setSourceModel(self.records)
        self.setModel(self.proxy)
        self.setAccessibleName(name)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.setSortingEnabled(True)
        self.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(44)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setMinimumSectionSize(90)
        self.horizontalHeader().setStretchLastSection(True)
        for i, column in enumerate(columns):
            self.setColumnWidth(i, column.width)

    def selected_record(self):
        index = self.proxy.mapToSource(self.currentIndex())
        return self.records.rows[index.row()] if index.isValid() else None

    def set_rows(self, rows: Sequence[Any]) -> None:
        selected = self.selected_record()
        key = self.row_key(selected) if selected is not None else None
        self.records.set_rows(rows)
        if selected is not None:
            for i, row in enumerate(self.records.rows):
                if self.row_key(row) == key:
                    self.setCurrentIndex(self.proxy.mapFromSource(self.records.index(i, 0)))
                    break
