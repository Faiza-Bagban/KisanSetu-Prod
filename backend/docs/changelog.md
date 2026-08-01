# Changelog

## 2026-07-31 — Groq + HF Inference migration
- Swapped local Ollama LLM calls (eligibility-ai, chatbot) for Groq API
  (llama-3.1-8b-instant) — free, no GPU needed, works on constrained hosting.
- Swapped local sentence-transformers embeddings for Hugging Face's
  hosted Inference API (router.huggingface.co) — removes PyTorch/embedding
  model from memory footprint.
- Both chatbot and eligibility-AI now fully functional on Render free tier
  staging (previously OOM'd / gracefully degraded).
- Root cause of earlier failures traced to Render's 512MB memory ceiling
  being exceeded by local model loading (BART classifier, MarianMT,
  sentence-transformers, PyTorch all in one process).