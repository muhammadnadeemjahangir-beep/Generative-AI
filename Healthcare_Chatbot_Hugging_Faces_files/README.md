---
title: AI Health Assistant
emoji: 🩺
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: mit
---

# 🩺 Vita — AI Health Assistant

A compact, professional pop-up style AI health assistant built with
**Gradio + LangChain + Groq**.

Vita offers general health information and guidance:
- 🤒 **Symptoms** — plain-language explanations, never a diagnosis
- 💊 **Medicines** — what they're generally used for (no dosing advice)
- 🥗 **Nutrition & lifestyle** — general, evidence-based tips
- 🩹 **First-aid basics** — for minor, non-emergency situations
- 🧠 **Mental health** — warm support with encouragement to seek professional help

This is **general information only, not a medical diagnosis** — always
consult a qualified healthcare provider for anything serious or urgent.

## Setup

This Space needs a Groq API key to run:

1. Go to this Space's **Settings → Repository secrets**.
2. Add a secret named `GROQ_API_KEY` with your key from
   [console.groq.com](https://console.groq.com).
3. Restart the Space if it's already running.

## Files

- `app.py` — the Gradio app (chat logic, system prompt, and custom CSS)
- `requirements.txt` — pinned Python dependencies
- `README.md` — this file, including the Spaces configuration header above
