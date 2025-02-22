#      ╔═══════════════════════════════════════╗
#
#                       Repo Grab                 
#
#      ╚═══════════════════════════════════════╝
#




import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


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
            process = subprocess.Popen(
                ["git-clone", self.repo_url, self.destination],  # Using 'git-clone' instead of 'git clone'
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            total_steps = 100  # Fake total steps for progress simulation
            progress = 0

            for line in process.stdout:
                self.output_signal.emit(line.strip())

                # Simulate progress based on common Git output messages
                if "Receiving objects:" in line:
                    percent = int(line.split("%")[0].split()[-1])  # Extract percentage
                    self.progress_signal.emit(percent)

            process.wait()

            if process.returncode == 0:
                self.output_signal.emit("✅ Clone completed successfully!")
                self.progress_signal.emit(100)  # Ensure full progress
            else:
                self.output_signal.emit("❌ Clone failed!")
                self.progress_signal.emit(0)

        except Exception as e:
            self.output_signal.emit(f"Error: {str(e)}")
            self.progress_signal.emit(0)


class GitCloneApp(QWidget):
    """Main GUI application for cloning GitHub repos with a progress bar."""
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("GitHub Repo Cloner")
        self.setGeometry(400, 200, 500, 350)

        layout = QVBoxLayout()

        self.label_url = QLabel("Enter GitHub Repository URL:")
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("https://github.com/user/repository.git")

        self.label_folder = QLabel("Select Destination Folder:")
        self.button_folder = QPushButton("Choose Folder")
        self.button_folder.clicked.connect(self.select_folder)

        self.clone_button = QPushButton("Clone Repository")
        self.clone_button.clicked.connect(self.clone_repository)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        layout.addWidget(self.label_url)
        layout.addWidget(self.input_url)
        layout.addWidget(self.label_folder)
        layout.addWidget(self.button_folder)
        layout.addWidget(self.clone_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.destination_folder = folder
            self.label_folder.setText(f"Destination: {folder}")

    def clone_repository(self):
        """Start cloning process."""
        repo_url = self.input_url.text().strip()
        if not repo_url:
            self.output_text.append("❌ Please enter a valid GitHub URL.")
            return

        if not hasattr(self, 'destination_folder'):
            self.output_text.append("❌ Please select a destination folder.")
            return

        self.output_text.append(f"🔄 Cloning {repo_url} into {self.destination_folder}...\n")
        self.progress_bar.setValue(0)  # Reset progress bar

        self.clone_thread = GitCloneThread(repo_url, self.destination_folder)
        self.clone_thread.output_signal.connect(self.update_output)
        self.clone_thread.progress_signal.connect(self.update_progress)
        self.clone_thread.start()

    def update_output(self, text):
        """Update the output log."""
        self.output_text.append(text)

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitCloneApp()
    window.show()
    sys.exit(app.exec_())
