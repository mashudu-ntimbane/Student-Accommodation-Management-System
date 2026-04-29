# 🎓 SAMS AI Chatbot

> **AI-powered student query assistant for the Student Accommodation Management System**

An NLP chatbot built with DistilBERT and Flask that classifies student queries into structured intents and returns contextual responses — integrated with a PHP backend via REST API.

---

## 📌 Project Overview

| Component | Technology |
|---|---|
| NLP Model | DistilBERT (fine-tuned) |
| API Server | Flask / FastAPI (Python) |
| Backend Integration | PHP + cURL |
| Frontend Widget | HTML + Vanilla JavaScript |
| Training Environment | Google Colab (GPU) |

**Intents handled:**
- `payment_query` — rent, fees, payment methods
- `rules_query` — smoking, noise, appliances, curfew
- `visitor_policy` — guest registration, visiting hours
- `application_status` — tracking, appeals, waiting lists
- `general_enquiry` — greetings, general help

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install transformers torch scikit-learn flask flask-cors accelerate seaborn
```

### 2. Train the model (Google Colab recommended)
```bash
# Upload to Colab and run
python 01_dataset_and_training.py
```

### 3. Start the API server
```bash
python 02_api_server.py
# API available at http://localhost:5000/chat
```

### 4. Test with curl
```bash
curl -X POST http://localhost:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "How do I pay my rent?"}'
```

Expected response:
```json
{
  "success": true,
  "intent": "payment_query",
  "confidence": 0.9821,
  "response": "Rent is due on the 1st of each month...",
  "method": "keyword"
}
```

### 5. PHP Integration
Update `CHATBOT_API_URL` in `03_php_integration.php` and include the chat widget in any SAMS page.

---

## 🗂️ Project Structure

```
sams_chatbot/
├── 01_dataset_and_training.py    # Dataset creation + DistilBERT training
├── 02_api_server.py              # Flask API + hybrid chatbot logic
├── 03_php_integration.php        # PHP cURL proxy + chat widget HTML/JS
├── SAMS_Chatbot_Complete.ipynb  # Google Colab notebook (all-in-one)
├── sams_chatbot_model/           # Saved model (generated after training)
│   ├── config.json
│   ├── pytorch_model.bin
│   ├── tokenizer_config.json
│   ├── label_mapping.json
│   └── responses.json
└── query_log.jsonl               # Auto-generated query log for retraining
```

---

## 🏗️ Architecture

```
Student Browser
      │  (JS fetch)
      ▼
PHP Controller (chat_endpoint.php)
      │  (cURL POST /chat)
      ▼
Flask API (Python · port 5000)
      │
      ├── Keyword Matcher (fast, rule-based)
      └── DistilBERT Classifier (ML fallback)
              │
              ▼
        Response Mapper → JSON response
```

---

## 🤖 Model Details

| Property | Value |
|---|---|
| Base model | `distilbert-base-uncased` |
| Task | Multi-class intent classification |
| Classes | 5 intents |
| Max sequence length | 64 tokens |
| Training epochs | 10 |
| Optimizer | AdamW (lr=2e-5, weight_decay=0.01) |
| Dataset size | ~100 synthetic examples |

**Hybrid approach:** The system first tries keyword matching (fast, ~0ms). If no keyword matches, DistilBERT classifies the intent. If confidence < 60%, a graceful fallback response is shown.

---

## 📊 Evaluation

After training you should see metrics like:

```
              precision  recall  f1-score  support
payment_query      0.95    1.00      0.97        4
rules_query        1.00    0.75      0.86        4
visitor_policy     1.00    1.00      1.00        4
application_status 1.00    1.00      1.00        4
general_enquiry    0.80    1.00      0.89        4

accuracy                             0.95       20
```

---

## ⚡ Deployment Options

| Option | Cost | Best for |
|---|---|---|
| **Local** (localhost) | Free | Development |
| **ngrok** | Free tier | Demos |
| **Railway.app** | Free tier | Small production |
| **Render.com** | Free tier | Persistent hosting |
| **AWS EC2 t3.micro** | ~$8/mo | Scalable production |

### Deploy to Render
1. Push this repo to GitHub
2. Connect at render.com → New Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `python 02_api_server.py`

---

## 🌍 Bonus: Improvements for v2

- **Multilingual support** — use `xlm-roberta-base` instead of DistilBERT to support Zulu, Afrikaans, Sotho, etc.
- **LLM API fallback** — when confidence < threshold, route to Claude or GPT for open-ended responses
- **Active learning** — export `query_log.jsonl`, label the `unknown` queries, and add them to training data
- **Conversation memory** — store session history for multi-turn conversations
- **Admin dashboard** — visualise intent frequencies from the query log

---

## 💼 Portfolio Presentation Tips

**GitHub README:** Add a GIF demo of the chat widget in action.  
**CV description:** *"Built an NLP intent classification chatbot using DistilBERT, integrated via REST API into a PHP accommodation management system, achieving 95%+ accuracy on a 5-class dataset."*  
**Live demo:** Deploy on Render and link from portfolio site.  
**Key skills demonstrated:** NLP · Transfer learning · REST API design · PHP/Python integration · Model evaluation · System design

---

## 📄 License

MIT — free to use and extend for your SAMS project.
