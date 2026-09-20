<div align="center">
  <h1>🌟 Polaris</h1>
  <p><b>A Deterministic Policy Reasoning Agent for the Modern Enterprise</b></p>
</div>

---

**Polaris** is an autonomous AI agent designed to answer complex employee policy questions reliably. It uses a **Hybrid Neuro-Symbolic architecture**, separating natural language understanding from the actual policy evaluation. This means it can converse like a human, but evaluate policies with 100% deterministic accuracy—eliminating AI hallucinations in compliance decisions.

## 📖 Table of Contents

- [How It Works](#-how-it-works)
- [Why Polaris?](#-why-polaris)
- [Getting Started](#-getting-started)
- [Using the API](#-using-the-api)

## ⚙️ How It Works

Polaris processes questions through a 4-step pipeline:

1. **Intent Classification**: The agent first determines if a question is general chat, a malicious prompt, or a genuine policy question.
2. **Context Parsing**: Instead of relying on standard semantic search (RAG), Polaris extracts strict, structured variables from the natural language query (e.g., `intent`, `role`, `department`, `region`).
3. **Deterministic Evaluation**: The extracted JSON context is fed into a rigid, deterministic Rule Engine. This engine resolves active dates, handles specific exceptions that override global rules, and identifies conflicting policies without ever guessing.
4. **Explanation**: The deterministic decision is handed back to the language model, which translates the dry JSON output into a polite, human-readable response citing exact policy IDs.

## ✨ Why Polaris?

- **Zero Hallucination Compliance**: By keeping the AI out of the decision-making step, you get 100% predictable and legally sound outcomes.
- **Conflict Escalation**: If two rules conflict, Polaris won't guess. It gracefully flags the conflict and provides managerial advice.
- **Audit Trails**: Every decision, the variables extracted, and the policies evaluated are logged as immutable JSON records for total transparency.

## 🚀 Getting Started

You can run Polaris locally on your own system. 

### Prerequisites
- Python 3.9+
- A compatible local LLM service running on your machine

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate the Seed Data:**
   Initialize your local JSON policy store with sample data.
   ```bash
   python scripts/seed_data.py
   ```

3. **Run the Application:**
   Start the FastAPI backend server.
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the UI:**
   Open your web browser and navigate to `http://localhost:8000`.

## 💻 Using the API

You can interact directly with the reasoning engine via the API. 

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/ask \
     -H "Content-Type: application/json" \
     -d '{
           "question": "Can the Analytics team share Dataset Y with Vendor X in India today?", 
           "context": {
               "region": "India", 
               "department": "Analytics"
           }
         }'
```
