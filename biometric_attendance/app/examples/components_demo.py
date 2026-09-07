"""Run with python -m biometric_attendance.app.examples.components_demo."""
import sys
from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QComboBox, QVBoxLayout, QWidget

from biometric_attendance.app.styles.theme import build_global_stylesheet, load_fonts
from biometric_attendance.app.widgets.components import Column, ContentState, FilterBar, PageHeader, RecordTable


@dataclass(frozen=True)
class ExampleRow:
    id: int
    name: str
    minutes: int | None


class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("ComponentDemo")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle("Component examples — sample data")
        self.resize(1000, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(PageHeader("Component examples", "Resize the window, sort columns, and explore each content state."))
        filters = FilterBar()
        self.mode = QComboBox()
        self.mode.addItems(["Content", "Loading", "Empty", "Error"])
        filters.add_field("&State", self.mode)
        layout.addWidget(filters)
        self.table = RecordTable([
            Column("Employee", lambda r: r.name, width=240),
            Column("Worked", lambda r: r.minutes, lambda value: f"{value} min"),
        ], name="Sample hours", row_key=lambda r: r.id)
        self.table.set_rows([ExampleRow(1, "Alex Rivera", 480), ExampleRow(2, "Sam Chen", 90), ExampleRow(3, "Taylor Cruz", None)])
        self.state = ContentState(self.table)
        layout.addWidget(self.state, 1)
        self.mode.currentTextChanged.connect(self.change_state)
        self.state.action_requested.connect(self.retry)

    def change_state(self, mode):
        if mode == "Content":
            self.state.show_content()
        elif mode == "Loading":
            self.state.show_state("loading", "Loading hours…", "This is an interactive component example.")
        elif mode == "Empty":
            self.state.show_state("empty", "No hours found", "Change your filters to see more results.")
        else:
            self.state.show_state("error", "Hours unavailable", "Your changes have been preserved.", action="Try again")

    def retry(self):
        self.mode.setCurrentText("Loading")
        QTimer.singleShot(500, lambda: self.mode.setCurrentText("Content"))


def main():
    app = QApplication(sys.argv)
    load_fonts()
    app.setStyleSheet(build_global_stylesheet())
    window = Demo()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
