#!/usr/bin/env python3

import sys

import keyboard

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

from ui.app_window import Ui_app_window
from ui.notification import Ui_notification_window

import resources_rc

style = QtCore.QFile(":/files/style.qcss")
style.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)


class ShortcutListener(QtCore.QThread):
  shortcut_triggered = QtCore.pyqtSignal(str)

  def __init__(self):
    super().__init__()

    self.shortcuts = {}


  def run(self):
    keyboard.wait()


  def add_shortcut(self, shortcut):
    if shortcut in self.shortcuts:
      return

    keyboard.add_hotkey(shortcut, lambda s=shortcut: self.shortcut_triggered.emit(s))
    self.shortcuts[shortcut] = len(self.shortcuts.keys())

  def remove_shortcut(self, shortcut):
    if self.shortcuts.get(shortcut) == None:
      return

    del self.shortcuts[shortcut]


class NotificationWindow(QtWidgets.QWidget, Ui_notification_window):
  def __init__(self):
    super().__init__()

    self.setupUi(self)
    self.setStyleSheet(" * { color: #c9d1d9; }\n QLabel#notification_icon { background-color: transparent; border: none; }\nQWidget#notification { border-radius: 8px; }\nQWidget#notification, QWidget#notification QWidget { background-color: #0d1117; }")

    self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
    self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    self.opacity = 1
    self.timeout = 1500

    self.timeout_timer = QtCore.QTimer()
    self.timeout_timer.setInterval(50)
    self.timeout_timer.timeout.connect(self.decrease_to_close)


  def notify(self, message):
    self.opacity = 1.0
    self.timeout_timer.start()

    self.notification_message.setText(message)
    self.show()


  def decrease_to_close(self):
    self.setWindowOpacity(self.opacity)
    self.opacity -= 0.05

    if self.opacity < 0.05:
      self.close()


class AppWindow(QtWidgets.QMainWindow, Ui_app_window):
  def __init__(self, app=None):
    super().__init__()

    self.setupUi(self)
    self.setStyleSheet(str(style.readAll(), "utf-8"))

    self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

    self.app = app

    self.default_shortcuts = {
      "Ctrl+C": "Copied!",
      "Ctrl+V": "Pasted!"
    }

    self.window_pos = None
    self.shortcut_idx = 0

    self.shortcut_listener = ShortcutListener()
    self.shortcut_listener.shortcut_triggered.connect(self.notify_shortcut)

    self.shortcut_listener.start()

    self.notification_window = NotificationWindow()

    self.status_bar = self.statusBar()
    self.status_bar.setStyleSheet("QStatusBar::item { border: none; }")

    self.status_label = QtWidgets.QLabel("")
    self.status_bar.addPermanentWidget(self.status_label)

    self.reset_status_label = QtCore.QTimer()
    self.reset_status_label.setInterval(2500)
    self.reset_status_label.timeout.connect(lambda: self.status_label.setText(""))
    self.reset_status_label.start()

    self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(":/icons/icons/monev.png"), parent=self.app)

    menu = QtWidgets.QMenu()
    show_action = menu.addAction("Show")
    quit_action = menu.addAction("Exit")

    show_action.triggered.connect(self.show)
    quit_action.triggered.connect(QtWidgets.qApp.quit)

    self.tray_icon.setContextMenu(menu)
    self.tray_icon.show()

    for shortcut, message in self.default_shortcuts.items():
      self.add_shortcut(shortcut, message)

    self.shortcuts_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.shortcuts_table.customContextMenuRequested.connect(self.show_shortcut_controls)

    self.setup_signals()
    self.refresh_shortcuts()


  def mousePressEvent(self, event):
    if event.button() == QtCore.Qt.LeftButton and self.title_bar.underMouse():
      self.window_pos = event.globalPos() - self.frameGeometry().topLeft()

    event.accept()


  def mouseMoveEvent(self, event):
    if event.buttons() == QtCore.Qt.LeftButton and self.window_pos:
      self.move(event.globalPos() - self.window_pos)

    event.accept()


  def mouseReleaseEvent(self, event):
    self.window_pos = None


  def setup_signals(self):
    self.close_btn.clicked.connect(self.close)
    self.minimize_btn.clicked.connect(self.hide)

    self.shortcut_input.keySequenceChanged.connect(self.has_shortcut)
    self.reset_shortcut_btn.clicked.connect(lambda: self.shortcut_input.setKeySequence(""))

    self.add_shortcut_btn.clicked.connect(self.add_shortcut)


  def setup_colors(self):
    palette = QtGui.QPalette()

    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0d1117"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#161b22"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#21262d"))

    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#c9d1d9"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#c9d1d9"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#c9d1d9"))

    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#21262d"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#58a6ff"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))

    self.setPalette(palette)


  def print_status(self, message, color="white"):
    self.status_label.setStyleSheet(f"color: {color}; border: none; font-size: 13px")
    self.status_label.setText(message)


  def notify_shortcut(self, shortcut):
    if (shortcut_id := self.shortcut_listener.shortcuts.get(shortcut)) == None:
      return

    for row in range(self.shortcuts_table.rowCount()):
      if self.shortcuts_table.item(row, 0).text() != str(shortcut_id):
        continue

      self.notification_window.notify(self.shortcuts_table.item(row, 2).text())


  def refresh_shortcuts(self):
    for row in range(self.shortcuts_table.rowCount()):
      shortcut_key = self.shortcuts_table.item(row, 1).text()
      self.shortcut_listener.add_shortcut(shortcut_key)


  def has_shortcut(self, value):
    self.add_shortcut_btn.setEnabled(bool(value))


  def add_shortcut(self, _shortcut="", _message=""):
    shortcut_seq = self.shortcut_input.keySequence()
    shortcut_id = len(self.shortcut_listener.shortcuts.keys())
    shortcut = _shortcut or shortcut_seq.toString()
    shortcut_message = _message or self.shortcut_message.text()

    if self.shortcut_listener.shortcuts.get(shortcut) != None:
      self.print_status("Shortcut already added", color="#ff2e2e")
      return

    shortcut_id_item = QtWidgets.QTableWidgetItem(f"{shortcut_id}")
    shortcut_item = QtWidgets.QTableWidgetItem(shortcut)
    shortcut_message_item = QtWidgets.QTableWidgetItem(shortcut_message)

    shortcut_id_item.setTextAlignment(QtCore.Qt.AlignCenter)
    shortcut_item.setTextAlignment(QtCore.Qt.AlignCenter)
    shortcut_message_item.setTextAlignment(QtCore.Qt.AlignCenter)

    self.shortcuts_table.insertRow(0)
    self.shortcuts_table.setItem(0, 0, shortcut_id_item)
    self.shortcuts_table.setItem(0, 1, shortcut_item)
    self.shortcuts_table.setItem(0, 2, shortcut_message_item)

    self.shortcut_listener.add_shortcut(shortcut)


  def show_shortcut_controls(self, pos):
    item = self.shortcuts_table.itemAt(pos)

    if not item:
      return

    menu = QtWidgets.QMenu()
    remove_action = menu.addAction("Remove")

    action = menu.exec_(self.shortcuts_table.viewport().mapToGlobal(pos))

    if action == remove_action:
      shortcut = self.shortcuts_table.item(item.row(), 1).text()
      self.shortcut_listener.remove_shortcut(shortcut)
      self.shortcuts_table.removeRow(item.row())


if __name__ == "__main__":
  app = QtWidgets.QApplication(sys.argv)

  window = AppWindow(app=app)
  window.show()
  window.setup_colors()

  sys.exit(app.exec_())
