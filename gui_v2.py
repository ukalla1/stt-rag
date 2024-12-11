import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, 
    QVBoxLayout, QHBoxLayout, QGridLayout, QPlainTextEdit, QFrame
)
from PyQt6.QtCore import Qt

from stt_v2 import listen_and_recognize, stop_listening_event
from rag import RAG_pipeline

class ConvoAid(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversational Aid System")
        self.setGeometry(100, 100, 800, 600)

        self.current_chunk_number = 0
        self.transcript = ""
        self.rag_instance = None

        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Conversational Aid System")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size:20px; font-weight:bold; background-color: lightgrey; color:black;")
        main_layout.addWidget(title_label)

        # Control frame
        control_frame = QFrame()
        control_frame_layout = QHBoxLayout(control_frame)
        control_frame.setFrameShape(QFrame.Shape.StyledPanel)
        control_frame.setStyleSheet("background-color: lightgrey; border:1px solid black; color:black;")
        main_layout.addWidget(control_frame)
        
        self.start_stt_button = QPushButton("Start STT")
        self.start_stt_button.setStyleSheet("font-size:14px; background-color: lightgrey; color:black;")
        self.start_stt_button.clicked.connect(self.start_stt)
        control_frame_layout.addWidget(self.start_stt_button)

        self.stop_stt_button = QPushButton("Stop STT")
        self.stop_stt_button.setStyleSheet("font-size:14px; background-color: lightgrey; color:black;")
        self.stop_stt_button.setEnabled(False)
        self.stop_stt_button.clicked.connect(self.stop_stt)
        control_frame_layout.addWidget(self.stop_stt_button)

        self.ask_llm_button = QPushButton("Ask LLM")
        self.ask_llm_button.setStyleSheet("font-size:14px; background-color: lightgrey; color:black;")
        self.ask_llm_button.clicked.connect(self.ask_llm)
        control_frame_layout.addWidget(self.ask_llm_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setStyleSheet("font-size:14px; background-color: lightgrey; color:black;")
        self.exit_button.clicked.connect(self.close)
        control_frame_layout.addWidget(self.exit_button)

        # Question input frame
        question_frame = QFrame()
        question_frame.setFrameShape(QFrame.Shape.StyledPanel)
        question_frame.setStyleSheet("background-color: lightgrey; border:1px solid black; color:black;")
        question_layout = QGridLayout(question_frame)
        main_layout.addWidget(question_frame)

        question_label = QLabel("Your Question:")
        question_label.setStyleSheet("font-size:14px; color:black;")
        question_layout.addWidget(question_label, 0, 0)

        self.question_entry = QLineEdit()
        self.question_entry.setStyleSheet("font-size:14px; background-color:white; color:black;")
        question_layout.addWidget(self.question_entry, 1, 0)

        self.submit_question_button = QPushButton("Submit")
        self.submit_question_button.setStyleSheet("font-size:14px; background-color: lightgrey; color:black;")
        self.submit_question_button.clicked.connect(self.submit_question)
        question_layout.addWidget(self.submit_question_button, 1, 1)

        # Transcript area
        self.transcript_area = QPlainTextEdit()
        self.transcript_area.setReadOnly(True)
        self.transcript_area.setStyleSheet("font-size:12px; background-color:white; color:black;")
        main_layout.addWidget(self.transcript_area, stretch=1)

    def start_stt(self):
        """Start the Speech-to-Text process."""
        self.transcript = ""
        self.start_stt_button.setEnabled(False)
        self.stop_stt_button.setEnabled(True)

        # Start STT in a separate thread
        stt_thread = threading.Thread(target=self.run_stt, daemon=True)
        stt_thread.start()

    def stop_stt(self):
        """Stop the Speech-to-Text process."""
        stop_listening_event.set()
        self.stop_stt_button.setEnabled(False)
        self.ask_llm_button.setEnabled(True)

    def run_stt(self):
        """STT process."""
        listen_and_recognize(self.current_chunk_number)
        self.current_chunk_number += 1
        # Directly append text (no QThread checks)
        self.append_transcript_text(f"Transcription saved as transcription_chunk_{self.current_chunk_number - 1}.pdf")

    def ask_llm(self):
        """Initialize the LLM process."""
        self.submit_question_button.setEnabled(True)
        self.question_entry.setEnabled(True)
        self.question_entry.clear()

        pdf_filename = f"transcription_chunk_{self.current_chunk_number - 1}.pdf"
        self.rag_instance = RAG_pipeline()
        try:
            docs = self.rag_instance.load_documents([pdf_filename])
            splits = self.rag_instance.split_documents(docs)
            self.rag_instance.create_vector_db(splits, persist_directory='docs/chroma/')
            self.rag_instance.build_qa_chain()
            self.append_transcript_text(f"Loaded {pdf_filename} into the LLM.")
        except Exception as e:
            self.append_transcript_text(f"Error loading transcription into LLM: {e}")

    def submit_question(self):
        """Submit a question to the LLM and display the answer."""
        question = self.question_entry.text()
        if not question.strip():
            QMessageBox.warning(self, "Warning", "Please enter a question.")
            return

        try:
            answer = self.rag_instance.generate_answer(question)
            self.append_transcript_text(f"Q: {question}\nA: {answer}")
        except Exception as e:
            self.append_transcript_text(f"Error generating answer: {e}")

    def append_transcript_text(self, text):
        """Append text to the transcript area."""
        # Directly append text.
        self.transcript_area.appendPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConvoAid()
    window.show()
    sys.exit(app.exec())
