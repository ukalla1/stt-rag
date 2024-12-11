import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from stt_v2 import listen_and_recognize, stop_listening_event
from rag import RAG_pipeline


class ConvoAid:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversational Aid System")
        self.root.geometry("800x600")

        self.current_chunk_number = 0
        self.transcript = ""
        self.rag_instance = None

        # Create UI Elements
        self.create_ui()

    def create_ui(self):
        # Title Label
        title_label = tk.Label(
            self.root,
            text="Conversational Aid System",
            font=("Arial", 20, "bold"),
            bg="lightgrey",
            fg="black"
        )
        title_label.pack(pady=10, fill=tk.X)

        # Control Buttons Frame
        control_frame = tk.Frame(self.root, bg="lightgrey", relief="groove", borderwidth=2)
        control_frame.pack(pady=10, fill=tk.X)

        self.start_stt_button = tk.Button(
            control_frame,
            text="Start STT",
            font=("Arial", 14),
            command=self.start_stt
        )
        self.start_stt_button.grid(row=0, column=0, padx=10, pady=5)

        self.stop_stt_button = tk.Button(
            control_frame,
            text="Stop STT",
            font=("Arial", 14),
            state=tk.DISABLED,
            command=self.stop_stt
        )
        self.stop_stt_button.grid(row=0, column=1, padx=10, pady=5)

        self.ask_llm_button = tk.Button(
            control_frame,
            text="Ask LLM",
            font=("Arial", 14),
            command=self.ask_llm
        )
        self.ask_llm_button.grid(row=0, column=2, padx=10, pady=5)

        self.exit_button = tk.Button(
            control_frame,
            text="Exit",
            font=("Arial", 14),
            command=self.root.quit
        )
        self.exit_button.grid(row=0, column=3, padx=10, pady=5)

        # Question Input Frame
        question_frame = tk.Frame(self.root, bg="lightgrey", relief="groove", borderwidth=2)
        question_frame.pack(pady=10, padx=10, fill=tk.X)

        # Label for Question
        question_label = tk.Label(
            question_frame,
            text="Your Question:",
            font=("Arial", 14),
            bg="lightgrey",
            fg="black"
        )
        question_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Entry field for questions
        self.question_entry = tk.Entry(
            question_frame,
            font=("Arial", 14),
            width=50,
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=2
        )
        self.question_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        question_frame.columnconfigure(0, weight=1)

        self.submit_question_button = tk.Button(
            question_frame,
            text="Submit",
            font=("Arial", 14),
            command=self.submit_question
        )
        self.submit_question_button.grid(row=1, column=1, padx=5, pady=5)

        # Transcript Area
        self.transcript_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Arial", 12),
            height=15,
            state=tk.DISABLED,
            bg="white",
            fg="black",
            relief="sunken",
            borderwidth=2
        )
        self.transcript_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def start_stt(self):
        """Start the Speech-to-Text process."""
        self.transcript = ""
        self.start_stt_button.config(state=tk.DISABLED)
        self.stop_stt_button.config(state=tk.NORMAL)

        # Start STT in a separate thread
        stt_thread = threading.Thread(target=self.run_stt, daemon=True)
        stt_thread.start()

    def stop_stt(self):
        """Stop the Speech-to-Text process."""
        stop_listening_event.set()
        self.stop_stt_button.config(state=tk.DISABLED)
        self.ask_llm_button.config(state=tk.NORMAL)

    def run_stt(self):
        """STT process."""
        listen_and_recognize(self.current_chunk_number)
        self.current_chunk_number += 1

        # Display the transcript
        self.update_transcript_area(f"Transcription saved as transcription_chunk_{self.current_chunk_number - 1}.pdf")

    def ask_llm(self):
        """Initialize the LLM process."""
        self.submit_question_button.config(state=tk.NORMAL)
        self.question_entry.config(state=tk.NORMAL)  # Enable the question entry field
        self.question_entry.delete(0, tk.END)  # Clear the input field

        # Load the latest transcription into RAG
        pdf_filename = f"transcription_chunk_{self.current_chunk_number - 1}.pdf"
        self.rag_instance = RAG_pipeline()
        try:
            docs = self.rag_instance.load_documents([pdf_filename])
            splits = self.rag_instance.split_documents(docs)
            self.rag_instance.create_vector_db(splits, persist_directory='docs/chroma/')
            self.rag_instance.build_qa_chain()
            self.update_transcript_area(f"Loaded {pdf_filename} into the LLM.")
        except Exception as e:
            self.update_transcript_area(f"Error loading transcription into LLM: {e}")

    def submit_question(self):
        """Submit a question to the LLM and display the answer."""
        question = self.question_entry.get()
        if not question.strip():
            messagebox.showwarning("Warning", "Please enter a question.")
            return

        try:
            answer = self.rag_instance.generate_answer(question)
            self.update_transcript_area(f"Q: {question}\nA: {answer}")
        except Exception as e:
            self.update_transcript_area(f"Error generating answer: {e}")

    def update_transcript_area(self, text):
        """Update the transcript display area."""
        self.transcript_area.config(state=tk.NORMAL)
        self.transcript_area.insert(tk.END, text + "\n")
        self.transcript_area.see(tk.END)
        self.transcript_area.config(state=tk.DISABLED)


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ConvoAid(root)
    root.mainloop()
