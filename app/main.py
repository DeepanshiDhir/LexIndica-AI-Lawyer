import sys
import os
import warnings
from pathlib import Path

# Add project root directory to sys.path so 'app' package resolves cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Suppress harmless third-party deprecation warnings for clean CLI output
warnings.filterwarnings("ignore")

# Set duplicate libomp flag for macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI backend server."""
    import uvicorn
    print(f"🚀 Starting Indian Legal AI Assistant Backend on http://{host}:{port}...")
    uvicorn.run("app.api.server:app", host=host, port=port, reload=True)


def run_frontend():
    """Start the Streamlit frontend."""
    import subprocess
    print("🎨 Starting Streamlit Frontend on http://localhost:8501...")
    subprocess.run(["streamlit", "run", "app/frontend/streamlit_app.py"])


def run_cli():
    """Run an interactive terminal chat session with LexIndica."""
    from app.api.server import get_graph
    print("=" * 65)
    print("⚖️  LexIndica: Indian Legal Intelligence Assistant (Terminal CLI)")
    print("Ask any question on tenant-landlord law, deposits, or eviction.")
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 65 + "\n")
    
    graph = get_graph()
    session_id = "terminal_cli_session"
    
    while True:
        try:
            query = input("\n👤 You: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye! Stay legally informed.")
                break
                
            print("\n⚖️ LexIndica is analyzing statutory provisions...")
            res = graph.run(query=query, session_id=session_id)
            print("\n" + res.final_response + "\n")
            if res.generated_document:
                print("\n" + "=" * 30 + " GENERATED DRAFT DOCUMENT " + "=" * 30)
                print(res.generated_document)
                print("=" * 86 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended.")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "frontend":
        run_frontend()
    elif len(sys.argv) > 1 and sys.argv[1] in ["cli", "terminal", "chat"]:
        run_cli()
    else:
        run_api()
