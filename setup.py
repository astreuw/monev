#!/usr/bin/env python

import os
import subprocess

import setuptools as st


class CompileUiCommand(st.Command):
  ui_dir = "ui/"

  description = "Compile all ui files"
  user_options = []


  def initialize_options(self):
      pass


  def finalize_options(self):
      pass


  def run(self):
    subprocess.run((["pyrcc5", "ui/resources.qrc", "-o", "resources_rc.py"]))

    if not os.path.exists(self.ui_dir):
      os.makedirs(self.ui_dir)

    for root, _, files in os.walk(self.ui_dir):
      for file in files:
        if not file.endswith(".ui"):
          continue

        ui_file = os.path.join(root, file)
        py_file = os.path.join(self.ui_dir, f"{os.path.splitext(file)[0]}.py")

        if not os.path.exists(py_file) or os.path.getmtime(ui_file) > os.path.getmtime(py_file):
          subprocess.run((["pyuic5", "-x", ui_file, "-o", py_file]))


class CompileAllCommand(st.Command):
  description = "Compile all files"
  user_options = []


  def initialize_options(self):
      pass


  def finalize_options(self):
      pass


  def run(self):
    self.run_command("compileui")

    subprocess.run(([
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--icon", "ui/icons/monev.ico",
        "--clean",
        "app.py"
    ]))


st.setup(
  name="monev",
  version="1.0",
  author="Ricardo Costa",
  author_email="astreuw@proton.me",
  description="Monitor every shortcut key",
  url="https://github.com/astreuw/monev",
  packages=["monev"],
  cmdclass={
    "compileui": CompileUiCommand,
    "compileall": CompileAllCommand,
  },
)
