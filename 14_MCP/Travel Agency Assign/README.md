---
title: TravelOps Client Intelligence Console
emoji: ✈️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.26.0
app_file: app.py
pinned: false
---

# ✈️ TravelOps Client Intelligence Console

An AI-powered travel operations platform built with **Gradio** and the **Model
Context Protocol (MCP)**. Upload a client's Excel travel data (flights,
bookings, hotels) and a company policy PDF, then use verified-data tools plus
Groq-powered AI assistants for support, trip planning, and travel advice.

Converted from the original `travel_agency_operation_mcp.ipynb` notebook for
deployment on Hugging Face Spaces.

## Features

- **Client Setup** — upload an Excel workbook (`Flights`, `Bookings`,
  `Hotels` sheets) and an optional policy PDF
- **Overview dashboard** — live KPI cards
- **Flight Search / Booking Tracking / Hotel Search** — backed by MCP tools
  that only use verified uploaded data
- **Refund Control** — refund requests are created as `Pending` and always
  require human approval
- **AI Support Assistant / Trip Planner / Travel Advisor** — powered by Groq,
  grounded in the verified client data and uploaded policy
- **MCP Explorer** — inspect the tools, resources, and prompts exposed by the
  underlying MCP server

## Required secret

This Space calls the Groq API for its AI features. Add a repository secret
named `GROQ_API_KEY` under **Settings → Repository secrets** (or **Variables
and secrets**) with your Groq API key. Without it, the app still runs and the
data-verification tools (flight/hotel search, booking tracking, refunds) work
normally — only the three AI-assistant tabs will show a configuration
message.

## Excel format

The uploaded workbook should contain sheets whose names include the words
`flight`, `booking`, and `hotel` (case-insensitive), e.g. `Flights`,
`Bookings`, `Hotels`.
