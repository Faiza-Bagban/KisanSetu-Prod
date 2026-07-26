import subprocess
import pytest

def ollama_available():
    try:
        import ollama
        models = ollama.list()
        model_names = [m.model for m in models.models]
        return any("llama3.1" in name for name in model_names)
    except Exception:
        return False

OLLAMA_UP = ollama_available()

def pytest_collection_modifyitems(items):
    for item in items:
        if "eligibility" in item.nodeid:
            if not OLLAMA_UP:
                item.add_marker(pytest.mark.skip(
                    reason="Ollama not available — GPU machine only"
                ))