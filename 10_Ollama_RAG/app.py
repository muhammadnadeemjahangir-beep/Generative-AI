import os
import re
import shutil
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from rag_pipeline import build_rag


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()


# --------------------------------------------------
# Global variables
# --------------------------------------------------
qa_chain = None
rag_stats = {}

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Clean Qwen thinking tags
# --------------------------------------------------
def clean_answer(text):
    """
    Some reasoning models may return <think>...</think>.
    This removes those tags from the final answer.
    """
    if text is None:
        return ""

    text = str(text)

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


# --------------------------------------------------
# Normalize uploaded files
# --------------------------------------------------
def normalize_uploaded_files(file_paths):
    if file_paths is None:
        return []

    if not isinstance(file_paths, list):
        file_paths = [file_paths]

    normalized_paths = []

    for file in file_paths:
        if file is None:
            continue

        if isinstance(file, str):
            source_path = Path(file)

        elif hasattr(file, "name"):
            source_path = Path(file.name)

        elif isinstance(file, dict):
            source_path = Path(file.get("name") or file.get("path"))

        else:
            continue

        if source_path.exists():
            normalized_paths.append(source_path)

    return normalized_paths


# --------------------------------------------------
# Dashboard
# --------------------------------------------------
def create_dashboard(stats):
    if not stats:
        return """
        <div style="
            padding:24px;
            border-radius:22px;
            background:linear-gradient(135deg,#f8fafc,#e2e8f0);
            border:1px solid #cbd5e1;
            color:#0f172a;
        ">
            <h2 style="color:#0f172a;">📊 Ollama RAG Dashboard</h2>
            <p style="color:#334155;">No documents indexed yet.</p>
            <p style="color:#334155;">
                Upload files and click <b>Upload & Index Documents</b>
                to see files, chunks, embeddings, and processing time.
            </p>
        </div>
        """

    total_files = stats.get("total_files", "N/A")
    total_documents = stats.get("total_documents", "N/A")
    total_chunks = stats.get("total_chunks", "N/A")
    embedding_model_name = stats.get(
        "embedding_model",
        os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large:latest")
    )
    vector_database = stats.get("vector_database", "FAISS")
    llm_model_name = stats.get(
        "llm_model",
        os.getenv("OLLAMA_LLM_MODEL", "qwen3:4b")
    )
    processing_time = stats.get("processing_time", "N/A")
    status = stats.get("status", "Ready with Ollama")

    return f"""
    <div style="
        padding:30px;
        border-radius:28px;
        background:
            radial-gradient(circle at top left, rgba(249,115,22,0.35), transparent 30%),
            radial-gradient(circle at top right, rgba(34,197,94,0.28), transparent 28%),
            linear-gradient(135deg,#020617,#0f172a 55%,#111827);
        color:white;
        box-shadow:0 25px 80px rgba(15,23,42,0.38);
        border:1px solid rgba(148,163,184,0.30);
    ">

        <h2 style="
            margin-bottom:8px;
            color:#ffffff;
            font-size:28px;
            font-weight:800;
        ">
            🦙 Ollama RAG Processing Dashboard
        </h2>

        <p style="
            color:#fed7aa;
            margin-bottom:24px;
            font-size:15px;
        ">
            Local RAG summary of document loading, chunking, embeddings,
            vector storage, and local LLM setup.
        </p>

        <div style="
            display:grid;
            grid-template-columns:repeat(3, 1fr);
            gap:18px;
        ">

            <div style="
                padding:20px;
                border-radius:20px;
                background:linear-gradient(135deg,rgba(37,99,235,0.35),rgba(30,64,175,0.22));
                border:1px solid rgba(147,197,253,0.45);
            ">
                <h3 style="color:#ffffff; font-size:18px;">📁 Files</h3>
                <p style="font-size:38px; font-weight:900; margin:0; color:#ffffff;">{total_files}</p>
                <p style="color:#bfdbfe;">Uploaded files</p>
            </div>

            <div style="
                padding:20px;
                border-radius:20px;
                background:linear-gradient(135deg,rgba(16,185,129,0.35),rgba(6,95,70,0.24));
                border:1px solid rgba(110,231,183,0.45);
            ">
                <h3 style="color:#ffffff; font-size:18px;">📄 Documents</h3>
                <p style="font-size:38px; font-weight:900; margin:0; color:#ffffff;">{total_documents}</p>
                <p style="color:#bbf7d0;">Loaded documents</p>
            </div>

            <div style="
                padding:20px;
                border-radius:20px;
                background:linear-gradient(135deg,rgba(147,51,234,0.38),rgba(88,28,135,0.26));
                border:1px solid rgba(216,180,254,0.45);
            ">
                <h3 style="color:#ffffff; font-size:18px;">🧩 Chunks</h3>
                <p style="font-size:38px; font-weight:900; margin:0; color:#ffffff;">{total_chunks}</p>
                <p style="color:#e9d5ff;">Text chunks created</p>
            </div>

            <div style="
                padding:20px;
                border-radius:20px;
                background:linear-gradient(135deg,rgba(14,165,233,0.35),rgba(12,74,110,0.26));
                border:1px solid rgba(125,211,252,0.45);
            ">
                <h3 style="color:#ffffff; font-size:18px;">🧠 Embeddings</h3>
                <p style="
                    color:#e0f2fe;
                    font-size:15px;
                    line-height:1.6;
                    word-break:break-word;
                    margin:0;
                ">
                    {embedding_model_name}
                </p>
            </div>

            <div style="
                padding:20px;
                border-radius:20px;
                background:linear-gradient(135deg,rgba(245,158,11,0.35),rgba(120,53,15,0.25));
                border:1px solid rgba(252,211,77,0.45);
            ">
                <h3 style="color:#ffffff; font-size:18px;">🗄️ Vector DB</h3>
                <p style="font-size:34px; font-weight:900; margin:0; color:#ffffff;">{vector_database}</p>
                <p style="color:#fde68a;">Vector storage</p>
            </div>

            <div style="
                padding:20px;
                border-radius:20px;
                background:linear-gradient(135deg,rgba(236,72,153,0.35),rgba(131,24,67,0.26));
                border:1px solid rgba(249,168,212,0.45);
            ">
                <h3 style="color:#ffffff; font-size:18px;">⚡ Processing Time</h3>
                <p style="font-size:34px; font-weight:900; margin:0; color:#ffffff;">{processing_time}</p>
                <p style="color:#fbcfe8;">seconds</p>
            </div>

        </div>

        <div style="
            margin-top:22px;
            padding:18px;
            border-radius:18px;
            background:rgba(255,255,255,0.10);
            border:1px solid rgba(255,255,255,0.18);
        ">
            <p style="color:#ffffff; margin:6px 0;">
                <b>🦙 Local LLM Model:</b>
                <span style="color:#fed7aa;">{llm_model_name}</span>
            </p>

            <p style="color:#ffffff; margin:6px 0;">
                <b>✅ RAG Status:</b>
                <span style="color:#86efac; font-weight:700;">{status}</span>
            </p>
        </div>

    </div>
    """


# --------------------------------------------------
# Upload and index documents
# --------------------------------------------------
def upload_files(file_paths):
    global qa_chain, rag_stats

    uploaded_files = normalize_uploaded_files(file_paths)

    if not uploaded_files:
        return (
            "⚠️ No valid files uploaded. Please upload PDF, DOCX, CSV, XLSX, MD, or TXT files.",
            create_dashboard({})
        )

    saved_paths = []

    try:
        for source_path in uploaded_files:
            destination_path = DATA_DIR / source_path.name

            if source_path.resolve() != destination_path.resolve():
                shutil.copy2(source_path, destination_path)

            saved_paths.append(str(destination_path))

        if not saved_paths:
            return (
                "⚠️ Files were selected, but no valid file path was found.",
                create_dashboard({})
            )

        qa_chain, rag_stats = build_rag(saved_paths)

        uploaded_list = "\n".join(
            [f"✅ {Path(path).name}" for path in saved_paths]
        )

        status_message = f"""
✅ Documents uploaded and indexed successfully using Ollama!

📂 Total files uploaded: {len(saved_paths)}

Uploaded files:
{uploaded_list}

You can now go to the Ask Questions tab and ask questions from your documents.
"""

        return status_message, create_dashboard(rag_stats)

    except ValueError as e:
        return (
            f"⚠️ {str(e)}",
            create_dashboard({})
        )

    except Exception as e:
        return (
            f"⚠️ Error while building RAG chain: {str(e)}",
            create_dashboard({})
        )


# --------------------------------------------------
# Ask question
# --------------------------------------------------
def ask_question(question):
    if qa_chain is None:
        return "⚠️ Please upload and index documents first."

    if not question or not question.strip():
        return "⚠️ Please enter a question."

    try:
        response = qa_chain.invoke(question)

        if hasattr(response, "content"):
            return clean_answer(response.content)

        if isinstance(response, dict):
            for key in ["answer", "result", "output_text"]:
                if key in response:
                    return clean_answer(response[key])

        return clean_answer(response)

    except Exception as e:
        return f"⚠️ Error while generating answer: {str(e)}"


def clear_upload_status():
    return "", create_dashboard({})


def clear_answer():
    return "", ""


# --------------------------------------------------
# CSS
# --------------------------------------------------
custom_css = """
.gradio-container {
    max-width: 1250px !important;
    margin: auto !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

#hero-section {
    padding: 38px;
    border-radius: 30px;
    background:
        radial-gradient(circle at top left, rgba(249,115,22,0.45), transparent 30%),
        radial-gradient(circle at top right, rgba(34,197,94,0.35), transparent 28%),
        linear-gradient(135deg, #020617, #0f172a 55%, #111827);
    color: white;
    box-shadow: 0 25px 80px rgba(15,23,42,0.35);
    margin-bottom: 25px;
    border: 1px solid rgba(148,163,184,0.25);
}

#hero-section h1 {
    font-size: 44px;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #fb923c, #22c55e, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

#hero-section p {
    font-size: 17px;
    color: #cbd5e1;
    line-height: 1.6;
}

.info-card {
    padding: 20px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(248,250,252,0.98), rgba(226,232,240,0.82));
    border: 1px solid rgba(148,163,184,0.35);
    margin-bottom: 15px;
    min-height: 150px;
}

.info-card h3 {
    color: #0f172a;
}

.info-card p {
    color: #334155;
}

.footer-note {
    text-align: center;
    color: #64748b;
    font-size: 14px;
    margin-top: 25px;
}
"""


# --------------------------------------------------
# Gradio UI
# --------------------------------------------------
with gr.Blocks(
    css=custom_css,
    title="Ollama RAG Application",
    theme=gr.themes.Soft()
) as demo:

    gr.HTML(
        """
        <div id="hero-section">
            <h1>🦙 Ollama RAG Application</h1>
            <p>
                A local document question-answering system using
                <b>LangChain + Ollama + FAISS + Gradio</b>.
            </p>
            <p>
                Upload documents, create local embeddings, build a vector database,
                and ask questions from your own files without using a cloud API.
            </p>
        </div>
        """
    )

    with gr.Row():
        with gr.Column():
            gr.HTML(
                """
                <div class="info-card">
                    <h3>📌 Supported File Types</h3>
                    <p>PDF, DOCX, CSV, XLSX, XLS, MD, and TXT files are supported.</p>
                    <p><b>Best test:</b> Start with TXT first.</p>
                </div>
                """
            )

        with gr.Column():
            gr.HTML(
                """
                <div class="info-card">
                    <h3>🦙 Local AI Setup</h3>
                    <p>
                        Uses your local Ollama models:
                        <b>qwen3:4b</b> for answers and
                        <b>mxbai-embed-large</b> for embeddings.
                    </p>
                </div>
                """
            )

        with gr.Column():
            gr.HTML(
                """
                <div class="info-card">
                    <h3>⚠️ Important Note</h3>
                    <p>
                        Scanned PDFs or image-based documents may not work without OCR.
                        Use text-based files for this version.
                    </p>
                </div>
                """
            )

    with gr.Tabs():

        with gr.Tab("📁 Upload & Index Documents"):

            gr.Markdown(
                """
                ### Step 1: Upload your documents

                Upload files and click **Upload & Index Documents**.
                The system will show files, documents, chunks, embedding model,
                vector database, and processing time.
                """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    file_upload = gr.File(
                        label="Upload Documents",
                        file_types=[
                            ".pdf",
                            ".docx",
                            ".csv",
                            ".xlsx",
                            ".xls",
                            ".md",
                            ".txt"
                        ],
                        file_count="multiple",
                        type="filepath"
                    )

                    upload_btn = gr.Button(
                        "🚀 Upload & Index Documents",
                        variant="primary",
                        size="lg"
                    )

                    clear_upload_btn = gr.Button("Clear Upload Status")

                    status = gr.Textbox(
                        label="Upload / Indexing Status",
                        interactive=False,
                        lines=12,
                        placeholder="Upload status will appear here..."
                    )

                with gr.Column(scale=2):
                    dashboard = gr.HTML(
                        value=create_dashboard({})
                    )

            upload_btn.click(
                fn=upload_files,
                inputs=file_upload,
                outputs=[status, dashboard]
            )

            clear_upload_btn.click(
                fn=clear_upload_status,
                inputs=None,
                outputs=[status, dashboard]
            )

        with gr.Tab("💬 Ask Questions"):

            gr.Markdown(
                """
                ### Step 2: Ask questions from your uploaded documents

                The app retrieves relevant chunks and sends them to your local Ollama model.
                """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    question = gr.Textbox(
                        label="Your Question",
                        placeholder="Example: What is RAG?",
                        lines=6
                    )

                    ask_btn = gr.Button(
                        "🦙 Generate Answer",
                        variant="primary",
                        size="lg"
                    )

                    clear_answer_btn = gr.Button("Clear Question & Answer")

                with gr.Column(scale=1):
                    answer = gr.Textbox(
                        label="Answer",
                        interactive=False,
                        lines=18,
                        placeholder="The answer will appear here..."
                    )

            ask_btn.click(
                fn=ask_question,
                inputs=question,
                outputs=answer
            )

            question.submit(
                fn=ask_question,
                inputs=question,
                outputs=answer
            )

            clear_answer_btn.click(
                fn=clear_answer,
                inputs=None,
                outputs=[question, answer]
            )

        with gr.Tab("🧠 How Ollama RAG Works"):

            gr.Markdown(
                """
                ## Local Ollama RAG Pipeline

                ```text
                1. User uploads documents
                2. Files are saved in the data folder
                3. Text is extracted from files
                4. Text is split into chunks
                5. Embeddings are created using mxbai-embed-large
                6. Chunks are stored in FAISS
                7. User asks a question
                8. Relevant chunks are retrieved
                9. qwen3:4b generates the answer
                ```

                ## Models used

                ```text
                LLM Model: qwen3:4b
                Embedding Model: mxbai-embed-large:latest
                Vector Database: FAISS
                ```

                ## Common errors

                ```text
                model not found
                ```

                Means the model name in `.env` does not match `ollama list`.

                ```text
                No text was extracted
                ```

                Means the file may be empty, scanned, or image-based.
                """
            )

        with gr.Tab("🎓 Student Lab Task"):

            gr.Markdown(
                """
                ## Student Lab Scenario

                You are building a local document question-answering assistant
                for an organization that does not want to send documents to the cloud.

                ## Required Tasks

                1. Run Ollama locally.
                2. Run this Gradio app.
                3. Upload a TXT file.
                4. Ask one question.
                5. Upload PDF or DOCX.
                6. Upload CSV or XLSX.
                7. Check the dashboard statistics.
                8. Explain what chunks and embeddings are.
                9. Compare Ollama RAG with Groq RAG.
                """
            )

    gr.HTML(
        """
        <div class="footer-note">
            Built for classroom learning using LangChain, Ollama, FAISS, and Gradio.
        </div>
        """
    )


demo.launch(debug=True)