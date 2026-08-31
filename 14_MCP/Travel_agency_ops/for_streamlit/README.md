---
title: TravelOps Client Intelligence Console
emoji: ✈️
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: "1.38"
app_file: app.py
pinned: false
---

# ✈️ TravelOps Client Intelligence Console

An AI-powered travel operations platform built with **Streamlit**. Upload a
client's Excel travel data (flights, bookings, hotels) and a company policy
PDF, then use verified-data tools plus Groq-powered AI assistants for
support, trip planning, and travel advice.

Converted from the original Gradio + MCP (`travel_agency_operation_mcp.ipynb`)
version for deployment at **https://travelagencyoperations.streamlit.app/**
on Streamlit Community Cloud.

> **Note on this conversion:** the original app exposed its data tools over
> the Model Context Protocol (an MCP server called through an async MCP
> client). Streamlit apps are single-process and rerun top-to-bottom on every
> interaction, so this version keeps the exact same tool logic (search
> flights/hotels, verify bookings, file refund requests, raise operational
> alerts) as plain Python functions reading from `st.session_state`, and
> lists them under the **MCP Explorer** tab for reference. Behavior for the
> end user is unchanged — every verified-data guarantee (never inventing
> flights, prices, or policy, refunds always `Pending`) is preserved.

## Features

- **Client Setup** (sidebar) — upload an Excel workbook (`Flights`,
  `Bookings`, `Hotels` sheets) and an optional policy PDF
- **Overview** — live KPI cards and operational alerts
- **Flight Search / Booking Tracking / Hotel Search** — backed by
  verified-data tools that only use uploaded client data
- **Refund Control** — refund requests are created as `Pending` and always
  require human approval
- **AI Support Assistant / Trip Planner / Travel Advisor** — powered by
  Groq, grounded in the verified client data and uploaded policy
- **MCP Explorer** — reference list of the tools, resources, and prompts the
  console is built on

## Deploying on Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, and this `README.md` to the GitHub
   repo backing `https://travelagencyoperations.streamlit.app/`.
2. In the app's settings on Streamlit Community Cloud, open
   **Settings → Secrets** and add:

   ```toml
   GROQ_API_KEY = "your-groq-api-key-here"
   ```

   Without it, the app still runs and the data-verification tabs (flight
   search, hotel search, booking tracking, refunds) work normally — only the
   three AI-assistant tabs will show a configuration message.
3. Set **Main file path** to `app.py` and deploy.

### Running locally

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your-groq-api-key-here   # optional, enables AI tabs
streamlit run app.py
```

## Excel format

The uploaded workbook should contain sheets whose names include the words
`flight`, `booking`, and `hotel` (case-insensitive), e.g. `Flights`,
`Bookings`, `Hotels`.
