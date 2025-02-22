import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class GitCloneThread(QThread):
    """Thread to run the git-clone command."""
    output_signal = pyqtSignal(str)

    def __init__(self, repo_url, destination):
        super().__init__()
        self.repo_url = repo_url
        self.destination = destination

    def run(self):
        try:
            process = subprocess.Popen(
                ["git-clone", self.repo_url, self.destination],  # <== Changed to 'git-clone'
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in process.stdout:
                self.output_signal.emit(line.strip())

            process.wait()
            if process.returncode == 0:
                self.output_signal.emit("✅ Clone completed successfully!")
            else:
                self.output_signal.emit("❌ Clone failed!")

        except Exception as e:
            self.output_signal.emit(f"Error: {str(e)}")


class GitCloneApp(QWidget):
    """Main GUI application for cloning GitHub repos."""
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("GitHub Repo Cloner")
        self.setGeometry(400, 200, 500, 300)

        layout = QVBoxLayout()

        self.label_url = QLabel("Enter GitHub Repository URL:")
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("https://github.com/user/repository.git")

        self.label_folder = QLabel("Select Destination Folder:")
        self.button_folder = QPushButton("Choose Folder")
        self.button_folder.clicked.connect(self.select_folder)

        self.clone_button = QPushButton("Clone Repository")
        self.clone_button.clicked.connect(self.clone_repository)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        layout.addWidget(self.label_url)
        layout.addWidget(self.input_url)
        layout.addWidget(self.label_folder)
        layout.addWidget(self.button_folder)
        layout.addWidget(self.clone_button)
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

        self.clone_thread = GitCloneThread(repo_url, self.destination_folder)
        self.clone_thread.output_signal.connect(self.update_output)
        self.clone_thread.start()

    def update_output(self, text):
        """Update the output log."""
        self.output_text.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitCloneApp()
    window.show()
    sys.exit(app.exec_())
