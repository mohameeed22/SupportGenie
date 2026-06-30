<div align="center">

# 🧞 SupportGenie

**AI-powered Telegram customer support bot — built for real Upwork deployments**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.6-blue?logo=telegram)](https://github.com/python-telegram-bot/python-telegram-bot)
[![Groq](https://img.shields.io/badge/AI-Groq%20%7C%20Llama%203.3%2070B-orange?logo=meta)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Ask product questions • Track orders • Browse FAQs • Escalate to humans — all from Telegram*

</div>

---

## 📖 What Is This?

**SupportGenie** is a production-ready Telegram bot that acts as an AI customer support agent for an e-commerce store. It demonstrates the full stack of skills clients ask for in real Telegram bot job postings:

- 🤖 **LLM integration** — Groq (Llama 3.3 70B) for near-instant AI responses (<1s)
- 💬 **Conversation memory** — remembers the last 10 message pairs per user
- 🧭 **Inline keyboard UX** — polished button menus, no commands needed
- 🔄 **Multi-step flows** — ConversationHandler for order tracking
- 📦 **Structured knowledge base** — system prompt injection with store data
- 🧑‍💼 **Smart escalation** — detects when to hand off to a human agent

The fake store used is **NovaBuy** — a fictional electronics & accessories brand.

---

## ✨ Features

| Feature | Details |
|---|---|
| `/start` welcome menu | 4 inline buttons, branded greeting |
| 📦 Order Tracking | Enter `NB-XXXXX` → get live status, tracking number, ETA |
| ❓ FAQ Browser | 6 instant answers (returns, shipping, payment, warranty, etc.) |
| 🛍️ Product Catalog | Browse all 10 products with stock status |
| 🤖 AI Free Chat | Ask anything — Genie answers using store context only |
| 🧑‍💼 Human Escalation | Smart handoff with support email + hours |
| 🔒 Out-of-scope guard | Politely declines unrelated questions instead of hallucinating |

---

## 🗂️ Project Structure

```
SupportGenie/
├── bot.py                  # Entry point — registers all handlers, starts polling
├── config.py               # Environment variable loader + validation
├── store_context.py        # Products, policies & AI system prompt (the "brain")
├── ai_handler.py           # Groq client + per-user conversation memory
│
├── handlers/
│   ├── start.py            # /start & /help — welcome message + inline menu
│   ├── menu.py             # Central callback router for all button presses
│   ├── faq.py              # 6 static FAQ topics with inline navigation
│   ├── order_tracking.py   # Multi-step order lookup (ConversationHandler)
│   └── fallback.py         # Human escalation + product catalog view
│
├── data/
│   └── mock_orders.json    # 10 realistic fake orders for demo
│
├── requirements.txt        # Python dependencies
├── .env.example            # Template — copy to .env and fill in your keys
└── .gitignore
```

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.10+
- A Telegram bot token (free from [@BotFather](https://t.me/BotFather))
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone the repo

```bash
git clone https://github.com/mohameeed22/SupportGenie.git
cd SupportGenie
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
TELEGRAM_BOT_TOKEN=your_token_from_botfather
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Run

```bash
python bot.py
```

You should see:
```
INFO | __main__ — SupportGenie Bot is starting...
INFO | __main__ — AI Model: llama-3.3-70b-versatile
INFO | telegram.ext.Application — Application started
```

Open your bot in Telegram and send `/start` 🎉

---

## 🧪 Demo Test Cases

| Scenario | How to trigger | Expected result |
|---|---|---|
| Welcome menu | `/start` | 4 inline buttons appear |
| Shipped order | Track → `NB-10042` | Carrier, tracking number, ETA |
| Delivered order | Track → `NB-10044` | Delivered date, return info |
| Cancelled order | Track → `NB-10046` | Cancel reason + refund status |
| Multi-item order | Track → `NB-10099` | Two products, FedEx tracking |
| AI product question | *"Do you have noise-cancelling earbuds?"* | Genie recommends SoundWave Pro |
| AI policy question | *"Can I return an opened keyboard?"* | Explains exchange/store credit |
| FAQ navigation | Tap ❓ → any topic | Instant answer + back buttons |
| Human escalation | Tap 🧑‍💼 | Support contact + FAQ suggestion |
| Out-of-scope | *"What's the weather in Paris?"* | Politely declines |

---

## ⚙️ Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | From @BotFather |
| `GROQ_API_KEY` | ✅ | — | From console.groq.com |
| `GROQ_MODEL` | ❌ | `llama-3.3-70b-versatile` | Any Groq-supported model |
| `SUPPORT_EMAIL` | ❌ | `support@novabuy.store` | Shown in escalation message |
| `SUPPORT_HOURS` | ❌ | `Mon–Fri, 9am–6pm EST` | Shown in escalation message |

---

## 🔧 Adapting for a Real Store

This project is designed to be a starting point. To use it with a real client:

1. **Products** → Update the `PRODUCTS` list in [`store_context.py`](store_context.py)
2. **Policies** → Update the `POLICIES` string in [`store_context.py`](store_context.py)
3. **Orders** → Replace the JSON file lookup in [`order_tracking.py`](handlers/order_tracking.py) with a real DB/API call
4. **Escalation** → Wire [`fallback.py`](handlers/fallback.py) to a CRM webhook (Freshdesk, Zendesk, etc.)
5. **AI Model** → Switch `GROQ_MODEL` in `.env` for speed/cost trade-offs:
   - `llama-3.3-70b-versatile` — most capable (default)
   - `llama-3.1-8b-instant` — fastest, lowest cost

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `python-telegram-bot` | 21.6 | Async Telegram bot framework |
| `groq` | 0.11.0 | Groq Python SDK |
| `python-dotenv` | 1.0.1 | `.env` file loader |
| `httpx` | 0.27.2 | HTTP client (pinned for Groq compatibility) |

---

## 📄 License

MIT — free to use, fork, and adapt for your own projects.

---

<div align="center">

Built by [Mohamed](https://github.com/mohameeed22) · Powered by [Groq](https://groq.com) + [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

</div>
