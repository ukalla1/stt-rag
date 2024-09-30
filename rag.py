import os
import openai
import sys
from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import datetime
import warnings
warnings.filterwarnings("ignore")

# Class definition
class RAG_pipeline:
    def __init__(self):
        self.load_environment_variables()
        self.initialize_directories()
        self.llm_name = self.select_llm()
        self.embeddings = OpenAIEmbeddings()
        self.vector_db = None

    def load_environment_variables(self):
        """Load API keys and environment variables."""
        _ = load_dotenv(find_dotenv())
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def initialize_directories(self):
        """Create necessary directories."""
        self.current_dir = os.getcwd()
        self.docs_dir = os.path.join(self.current_dir, 'docs')
        self.chroma_dir = os.path.join(self.docs_dir, 'chroma')

        # Create 'docs' and 'chroma' directories if they don't exist
        if not os.path.isdir(self.docs_dir):
            os.mkdir(self.docs_dir)
            print(f"Created directory: {self.docs_dir}")
        if not os.path.exists(self.chroma_dir):
            os.mkdir(self.chroma_dir)
            print(f"Created subfolder: {self.chroma_dir}")

    def select_llm(self):
        """Select which language model to use based on the date."""
        current_date = datetime.datetime.now().date()
        if current_date < datetime.date(2023, 9, 2):
            return "gpt-3.5-turbo-0301"
        else:
            return "gpt-3.5-turbo"

    def load_documents(self, pdf_files):
        """Load documents from PDF files."""
        loaders = [PyPDFLoader(pdf) for pdf in pdf_files]
        docs = []
        for loader in loaders:
            docs.extend(loader.load())
        return docs

    def split_documents(self, docs, chunk_size=2048):
        """Split documents into smaller chunks."""
        chunk_overlap=int(chunk_size / 10)
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return text_splitter.split_documents(docs)

    def create_vector_db(self, docs, persist_directory):
        """Create a vector database from document chunks."""
        vectordb = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        self.vector_db = vectordb
        return vectordb

    def build_qa_chain(self):
        """Build a QA chain for querying the documents."""
        prompt_template = """You are analyzing reviews for a paper. The reviews include a meta review and detailed reviews from official reviewers.
        The reviews should help you answer the following question. Each review contains summary, strengths, weaknesses, and detailed feedback.
        Context: {context}
        Question: {question}
        Answer based on the information provided:"""
        
        self.QA_CHAIN_PROMPT = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(model_name=self.llm_name, temperature=0.5)

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=self.vector_db.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.QA_CHAIN_PROMPT}
        )

    def generate_answer(self, question, k=3):
        """Retrieve context and generate an answer for the given question."""
        docs = self.vector_db.similarity_search(question, k=k)
        context_window = ' '.join([doc.page_content for doc in docs])
        prompt = self.QA_CHAIN_PROMPT.format(context=context_window, question=question)
        
        result = self.qa_chain({"query": prompt})
        return result['result']

def main():
    # Instantiate the class
    analyzer = RAG_pipeline()

    # Load the documents
    pdf_files = ["/app/source/reviewer_1.pdf"]  # Add other PDFs if needed
    docs = analyzer.load_documents(pdf_files)

    # Split documents into smaller chunks
    splits = analyzer.split_documents(docs, chunk_size=2048)

    # Create vector database
    vectordb = analyzer.create_vector_db(splits, persist_directory='docs/chroma/')
    k = vectordb._collection.count()

    # Build the QA chain
    analyzer.build_qa_chain()

    # Ask user for the question
    user_question = input("Please enter your question: ")

    # Generate the answer for the user-provided question
    answer = analyzer.generate_answer(user_question, k=k)

    # Print the result
    print(f"Answer: {answer}")

if __name__ == "__main__":
    main()