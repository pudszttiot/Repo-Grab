import sys
import os
import re
import subprocess
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QIcon

VERSION = "1.0.6"
GITHUB_REPO = "https://api.github.com/repos/pudszttiot/Repo-Grab/releases/latest"

class GitCloneThread(QThread):
    """Thread to run the git-clone command with progress tracking."""
    
    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, repo_url, destination):
        super().__init__()
        self.repo_url = repo_url
        self.destination = destination

    def run(self):
        try:
            startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
            if startupinfo:
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                ["git-clone", self.repo_url, self.destination],  
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                startupinfo=startupinfo
            )

            progress_pattern = re.compile(r"Receiving objects:\s+(\d+)%")

            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                self.output_signal.emit(line)

                match = progress_pattern.search(line)
                if match:
                    self.progress_signal.emit(int(match.group(1)))

            process.wait()
            self.progress_signal.emit(100 if process.returncode == 0 else 0)
            self.output_signal.emit("✅ Clone completed successfully!" if process.returncode == 0 else "❌ Clone failed!")

        except Exception as e:
            self.output_signal.emit(f"❌ Error: {str(e)}")
            self.progress_signal.emit(0)

class GitCloneApp(QWidget):
    """Main GUI application for cloning GitHub repos with a progress bar."""

    def __init__(self):
        super().__init__()
        self.destination_folder = ""
        self.initUI()

    def initUI(self):
        """Initialize UI elements."""
        self.setWindowTitle("Repo Grab")
        self.setWindowIcon(QIcon(r"../Images/Repo_Grab_3.png"))
        self.setGeometry(400, 200, 500, 400)

        layout = QVBoxLayout()

        # Add logo image at the top and centered
        self.logo_label = QLabel(self)
        pixmap = QPixmap(r"../Images/Repo_Grab_3.png")  # Ensure logo.png is in the same directory or specify full path
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.logo_label)

        self.input_url = self.create_line_edit("Enter GitHub Repository URL:", "https://github.com/user/repository.git")
        self.label_folder, self.button_folder = self.create_folder_selector()
        
        self.clone_button = self.create_button("Clone Repository", self.clone_repository, enabled=False)
        self.update_button = self.create_button("Check for Updates", self.check_for_updates)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        layout.addWidget(self.input_url)
        layout.addWidget(self.label_folder)
        layout.addWidget(self.button_folder)
        layout.addWidget(self.clone_button)
        layout.addWidget(self.update_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def create_line_edit(self, label_text, placeholder=""):
        """Create a labeled QLineEdit."""
        label = QLabel(label_text)
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        return line_edit

    def create_folder_selector(self):
        """Create a folder selection button with a label."""
        label = QLabel("Select Destination Folder:")
        button = QPushButton("Choose Folder")
        button.clicked.connect(self.select_folder)
        return label, button

    def create_button(self, text, callback, enabled=True):
        """Create a QPushButton with a click event."""
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setEnabled(enabled)
        return button

    def select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.destination_folder = folder
            self.label_folder.setText(f"Destination: {folder}")
            self.clone_button.setEnabled(True)

    def clone_repository(self):
        """Start cloning process."""
        repo_url = self.input_url.text().strip()
        if not repo_url:
            return self.show_error("Please enter a valid GitHub URL.")
        if not self.destination_folder:
            return self.show_error("Please select a destination folder.")

        self.output_text.append(f"🔄 Cloning {repo_url} into {self.destination_folder}...\n")
        self.progress_bar.setValue(0)

        self.clone_thread = GitCloneThread(repo_url, self.destination_folder)
        self.clone_thread.output_signal.connect(self.update_output)
        self.clone_thread.progress_signal.connect(self.update_progress)
        self.clone_thread.start()

    def check_for_updates(self):
        """Check for the latest version on GitHub."""
        try:
            response = requests.get(GITHUB_REPO, timeout=5)
            if response.status_code == 200:
                latest_version = response.json().get("tag_name", "Unknown")
                message = (
                    f"⚠️ New version available: {latest_version}. Please update."
                    if latest_version != VERSION else "✅ You have the latest version."
                )
                self.output_text.append(message)
            else:
                self.show_error("Failed to check for updates.")
        except requests.RequestException as e:
            self.show_error(f"Error checking updates: {e}")

    def update_output(self, text):
        """Update the output log."""
        self.output_text.append(text)

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def show_error(self, message):
        """Display an error message."""
        QMessageBox.critical(self, "Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if os.path.exists("style.qss"):
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())

    window = GitCloneApp()
    window.show()
    sys.exit(app.exec_())
