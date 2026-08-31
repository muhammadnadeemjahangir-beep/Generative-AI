"""
TravelOps Client Intelligence Console — Streamlit Edition
Converted from the Gradio + MCP notebook-export version for deployment
on Streamlit Community Cloud (https://travelagencyoperations.streamlit.app/).

Upload a client's Excel travel data (Flights / Bookings / Hotels sheets) and
an optional company policy PDF, then use verified-data tools plus
Groq-powered AI assistants for support, trip planning, and travel advice.
"""

import os
import json

import pandas as pd
import streamlit as st
from pypdf import PdfReader

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TravelOps Client Intelligence Console",
    page_icon="✈️",
    layout="wide",
)

GROQ_MODEL = "openai/gpt-oss-20b"


# ============================================================
# STYLE (adapted from the original Gradio CSS)
# ============================================================

CSS = """
<style>
.stApp {
    background: linear-gradient(135deg, #ffffff, #faf5ff, #fff5fa);
}

.kpis {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}
@media (max-width: 900px) {
    .kpis { grid-template-columns: repeat(2, 1fr); }
}

.kpi {
    background: white;
    border: 1px solid #ddc7ef;
    border-radius: 20px;
    padding: 18px;
    box-shadow: 0 10px 28px rgba(124,58,237,.09);
}
.kpi small { display: block; color: #6b4d7d; }
.kpi b { display: block; color: #291039; font-size: 25px; }
.kpi span { color: #694e79; font-size: 13px; }
.kicon { font-size: 25px; color: #7e22ce; }

.detail {
    background: white;
    border: 1px solid #dfc9f4;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 12px;
}
.detail small { color: #6b4d7d; }
.detail h3 { margin: 4px 0; color: #291039; }

.metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 20px;
}
@media (max-width: 900px) {
    .metrics { grid-template-columns: repeat(2, 1fr); }
}
.metrics div { background: #fcf9ff; border: 1px solid #eadcff; border-radius: 12px; padding: 14px; }
.metrics small { display: block; color: #6b4d7d; }
.metrics b { display: block; margin-top: 5px; color: #291039; }

.success {
    background: #f0fdf6; color: #065f46; border: 1px solid #bdf0d6;
    border-radius: 15px; padding: 16px;
}
.error {
    background: #fff1f7; color: #9f1239; border: 1px solid #f9c8df;
    border-radius: 15px; padding: 16px;
}
.alert-ok { background: #f0fdf6; color: #065f46; border: 1px solid #bdf0d6; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; }
.alert-warn { background: #fff8eb; color: #92400e; border: 1px solid #fde3a7; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "flights": pd.DataFrame(),
        "bookings": pd.DataFrame(),
        "hotels": pd.DataFrame(),
        "policy_text": "",
        "refund_requests": [],
        "booking_requests": [],
        "load_message": "",
        "load_ok": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.getenv("GROQ_API_KEY")
    if not api_key or Groq is None:
        return None
    return Groq(api_key=api_key)


groq_client = get_groq_client()


# ============================================================
# DATA LOADING
# ============================================================

def clean_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def load_client_workspace(excel_file, policy_file):
    """Load an uploaded Excel workbook + optional policy PDF into session state."""
    if excel_file is None:
        return False, "Please upload the client's Excel file first."

    try:
        excel = pd.ExcelFile(excel_file)

        flights = pd.DataFrame()
        bookings = pd.DataFrame()
        hotels = pd.DataFrame()

        for sheet in excel.sheet_names:
            df = clean_columns(pd.read_excel(excel, sheet_name=sheet))
            name = sheet.lower().strip()
            if "flight" in name:
                flights = df
            elif "booking" in name:
                bookings = df
            elif "hotel" in name:
                hotels = df

        st.session_state["flights"] = flights
        st.session_state["bookings"] = bookings
        st.session_state["hotels"] = hotels
        st.session_state["refund_requests"] = []
        st.session_state["booking_requests"] = []

        policy_text = ""
        if policy_file is not None:
            try:
                reader = PdfReader(policy_file)
                policy_text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                ).strip()
            except Exception:
                policy_text = "Policy PDF uploaded, but text extraction failed."
        st.session_state["policy_text"] = policy_text

        msg = (
            f"Client workspace loaded — Flights: {len(flights)}, "
            f"Bookings: {len(bookings)}, Hotels: {len(hotels)}, "
            f"Policy: {'Uploaded' if policy_text else 'Not uploaded'}"
        )
        return True, msg

    except Exception as e:
        return False, f"Workspace loading failed: {type(e).__name__}: {e}"


# ============================================================
# VERIFIED DATA TOOLS
# (equivalent to the original MCP tool set — plain functions
#  operating on st.session_state instead of module globals,
#  so each visitor's session stays isolated)
# ============================================================

def search_flights(origin="", destination="", limit=50):
    df = st.session_state["flights"].copy()
    if df.empty:
        raise ValueError("Client flight data has not been uploaded.")

    origin = (origin or "").strip().upper()
    destination = (destination or "").strip().upper()

    if origin and "origin" in df.columns:
        df = df[df["origin"].astype(str).str.upper().str.contains(origin, na=False)]
    if destination and "destination" in df.columns:
        df = df[df["destination"].astype(str).str.upper().str.contains(destination, na=False)]

    return df.head(limit)


def search_hotels(city="", room_type="", limit=50):
    df = st.session_state["hotels"].copy()
    if df.empty:
        raise ValueError("Client hotel data has not been uploaded.")

    city = (city or "").strip()
    room_type = (room_type or "").strip()

    if city and "city" in df.columns:
        df = df[df["city"].astype(str).str.contains(city, case=False, na=False)]
    if room_type and "room_type" in df.columns:
        df = df[df["room_type"].astype(str).str.contains(room_type, case=False, na=False)]

    return df.head(limit)


def get_booking_status(booking_id):
    bookings = st.session_state["bookings"].copy()
    flights = st.session_state["flights"].copy()

    if bookings.empty:
        raise ValueError("Client booking data has not been uploaded.")

    booking_id = (booking_id or "").strip().upper()
    bookings["_id"] = bookings["booking_id"].astype(str).str.upper()
    row = bookings[bookings["_id"] == booking_id]

    if row.empty:
        raise ValueError(f"Booking {booking_id} was not found.")

    booking = row.iloc[0]
    flights["_id"] = flights["flight_id"].astype(str).str.upper()
    frow = flights[flights["_id"] == str(booking["flight_id"]).upper()]

    if frow.empty:
        raise ValueError(f"Flight {booking['flight_id']} was not found.")

    flight = frow.iloc[0]

    return {
        "booking_id": str(booking["booking_id"]),
        "customer_name": str(booking["customer_name"]),
        "flight_id": str(booking["flight_id"]),
        "airline": str(flight["airline"]),
        "origin": str(flight["origin"]),
        "destination": str(flight["destination"]),
        "passengers": int(booking["passengers"]),
        "status": str(booking["status"]),
        "amount": float(booking["amount"]),
        "departure": str(flight["departure"]),
        "arrival": str(flight["arrival"]),
    }


def create_refund_request(booking_id, reason="Customer cancellation"):
    booking = get_booking_status(booking_id)  # raises if invalid — always verify first

    request_id = len(st.session_state["refund_requests"]) + 1
    request = {
        "request_id": request_id,
        "booking_id": booking["booking_id"],
        "amount": booking["amount"],
        "reason": reason,
        "status": "Pending",
    }
    st.session_state["refund_requests"].append(request)
    return request


def refund_table():
    if not st.session_state["refund_requests"]:
        return pd.DataFrame(columns=["request_id", "booking_id", "amount", "reason", "status"])
    return pd.DataFrame(st.session_state["refund_requests"])


def get_operational_alerts():
    alerts = []
    flights = st.session_state["flights"]
    bookings = st.session_state["bookings"]
    refunds = st.session_state["refund_requests"]

    if flights.empty and bookings.empty and not refunds:
        return ["No client travel data has been uploaded."]

    if not flights.empty and "status" in flights.columns:
        cancelled = flights[flights["status"].astype(str).str.lower().eq("cancelled")]
        if not cancelled.empty:
            alerts.append(f"{len(cancelled)} flight(s) are cancelled.")

        unavailable = flights[
            flights["status"].astype(str).str.lower().isin(["unavailable", "sold out"])
        ]
        if not unavailable.empty:
            alerts.append(f"{len(unavailable)} flight(s) are unavailable.")

    if not bookings.empty and "status" in bookings.columns:
        pending = bookings[bookings["status"].astype(str).str.lower().eq("pending")]
        if not pending.empty:
            alerts.append(f"{len(pending)} booking(s) are pending.")

    pending_refunds = [r for r in refunds if str(r["status"]).lower() == "pending"]
    if pending_refunds:
        alerts.append(f"{len(pending_refunds)} refund request(s) require human approval.")

    if not alerts:
        alerts.append("No critical operational alerts detected.")

    return alerts


def policy_text():
    return st.session_state["policy_text"] or "No client policy PDF has been uploaded."


def choice_lists():
    flights = st.session_state["flights"]
    bookings = st.session_state["bookings"]
    hotels = st.session_state["hotels"]

    origins = (
        sorted(flights["origin"].dropna().astype(str).str.strip().unique().tolist())
        if not flights.empty and "origin" in flights.columns else []
    )
    destinations = (
        sorted(flights["destination"].dropna().astype(str).str.strip().unique().tolist())
        if not flights.empty and "destination" in flights.columns else []
    )
    booking_ids = (
        sorted(bookings["booking_id"].dropna().astype(str).str.strip().unique().tolist())
        if not bookings.empty and "booking_id" in bookings.columns else []
    )
    cities = (
        sorted(hotels["city"].dropna().astype(str).str.strip().unique().tolist())
        if not hotels.empty and "city" in hotels.columns else []
    )
    dates = (
        sorted(
            pd.to_datetime(flights["departure"], errors="coerce")
            .dropna().dt.strftime("%Y-%m-%d").unique().tolist()
        )
        if not flights.empty and "departure" in flights.columns else []
    )
    all_destinations = sorted(set(destinations + cities))
    preferences = ["Luxury", "Budget", "Family", "Business", "Beach", "Convenient location"]

    return {
        "origins": origins,
        "destinations": destinations,
        "booking_ids": booking_ids,
        "cities": cities,
        "dates": dates,
        "all_destinations": all_destinations,
        "preferences": preferences,
    }


# ============================================================
# AI ASSISTANTS (Groq)
# ============================================================

def ai_support(booking_id, issue):
    if not booking_id:
        return "❌ Please enter a Booking ID.", ""
    if not issue:
        return "❌ Please enter the customer's question.", ""
    if groq_client is None:
        return (
            "❌ GROQ_API_KEY is not configured for this app. "
            "Add it under Streamlit **Settings → Secrets**.",
            "",
        )

    try:
        booking = get_booking_status(booking_id)
    except Exception as e:
        return f"❌ Booking could not be verified: {e}", ""

    policy = policy_text()

    prompt = f"""
You are a professional travel customer support AI.

Your job is to help a travel company's customer support team.

VERIFIED BOOKING DATA:
{json.dumps(booking, indent=2)}

CUSTOMER QUESTION:
{issue}

COMPANY CANCELLATION POLICY:
{policy}

COMPANY REFUND POLICY:
{policy}

Instructions:

1. Use the verified booking data.
2. Use only the provided company policies for cancellation and refund decisions.
3. Never invent a policy.
4. Never invent booking information.
5. If information is unavailable, clearly say so.
6. Give a professional customer-friendly response.
7. If human approval is required, clearly mention it.

Return:

- Customer Response
- Booking Information
- Policy Guidance
- Next Action
"""

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional travel customer support AI."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=1500,
        )
        answer = response.choices[0].message.content
        evidence = (
            "### Verified Booking\n\n```json\n"
            + json.dumps(booking, indent=2)
            + "\n```\n\n### Cancellation Policy\n\n"
            + policy
            + "\n\n### Refund Policy\n\n"
            + policy
        )
        return answer, evidence
    except Exception as e:
        return f"❌ Support AI Error\n\n`{type(e).__name__}: {e}`", ""


def ai_trip_planner(destination, dates, budget):
    if not destination:
        return "❌ Please select a destination.", pd.DataFrame()
    if groq_client is None:
        return (
            "❌ GROQ_API_KEY is not configured for this app. "
            "Add it under Streamlit **Settings → Secrets**.",
            pd.DataFrame(),
        )

    try:
        hotel_df = search_hotels(city=destination, limit=20)
    except Exception as e:
        return f"⚠️ {e}", pd.DataFrame()

    hotel_data = hotel_df.to_dict(orient="records") if not hotel_df.empty else []

    prompt = f"""
You are an AI travel planning assistant for a professional travel agency.

Destination:
{destination}

Travel dates:
{dates}

Customer budget:
{budget}

VERIFIED CLIENT HOTEL DATA:
{json.dumps(hotel_data, indent=2)}

Create a useful travel plan.

Include:

1. Recommended hotel from verified data
2. Why the hotel fits
3. Day-by-day itinerary
4. Activities
5. Budget considerations
6. Travel tips

IMPORTANT:

- Never invent hotel availability.
- Never invent hotel prices.
- Never claim a hotel is available unless it appears in the verified data.
- If hotel data is empty, clearly say that no client hotel data was found.
- General activities may be recommendations, but label them as recommendations.
"""

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert AI travel planner."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_completion_tokens=1800,
        )
        answer = response.choices[0].message.content
        return answer, hotel_df
    except Exception as e:
        return f"❌ Trip Planner Error\n\n`{type(e).__name__}: {e}`", pd.DataFrame()


def ai_travel_advisor(destination, budget, preference):
    if not destination:
        return "❌ Please select a destination.", pd.DataFrame()
    if groq_client is None:
        return (
            "❌ GROQ_API_KEY is not configured for this app. "
            "Add it under Streamlit **Settings → Secrets**.",
            pd.DataFrame(),
        )

    try:
        hotel_df = search_hotels(city=destination, limit=20)
    except Exception as e:
        return f"⚠️ {e}", pd.DataFrame()

    hotel_data = hotel_df.to_dict(orient="records") if not hotel_df.empty else []

    prompt = f"""
You are an AI travel advisor working for a professional travel agency.

Destination:
{destination}

Customer budget:
{budget}

Customer preference:
{preference}

VERIFIED CLIENT HOTEL DATA:
{json.dumps(hotel_data, indent=2)}

Give practical travel advice.

Include:

1. Best suitable hotel
2. Why it matches the preference
3. Recommended activities
4. Budget considerations
5. Travel tips

RULES:

- Use verified client data for hotels.
- Do not invent hotel prices.
- Do not invent availability.
- Clearly distinguish verified information from general recommendations.
"""

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert AI travel advisor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_completion_tokens=1800,
        )
        answer = response.choices[0].message.content
        return answer, hotel_df
    except Exception as e:
        return f"❌ Travel Advisor Error\n\n`{type(e).__name__}: {e}`", pd.DataFrame()


# ============================================================
# SIDEBAR — CLIENT SETUP
# ============================================================

with st.sidebar:
    st.markdown("## 📁 Client Setup")
    excel_upload = st.file_uploader("Client Excel Workbook", type=["xlsx", "xls"])
    policy_upload = st.file_uploader("Company Policy PDF (optional)", type=["pdf"])

    if st.button("🚀 Load Client Workspace", use_container_width=True):
        ok, msg = load_client_workspace(excel_upload, policy_upload)
        st.session_state["load_ok"] = ok
        st.session_state["load_message"] = msg

    if st.session_state["load_message"]:
        if st.session_state["load_ok"]:
            st.success(st.session_state["load_message"])
        else:
            st.error(st.session_state["load_message"])

    st.caption(
        "Excel sheet names should include the words **flight**, **booking**, "
        "and **hotel** (case-insensitive)."
    )

    st.divider()
    if groq_client is None:
        st.warning(
            "⚠️ GROQ_API_KEY not set. The AI Support / Trip Planner / "
            "Travel Advisor tabs won't work until it's added under "
            "**Settings → Secrets**."
        )
    else:
        st.caption("✅ Groq AI configured.")


# ============================================================
# HEADER
# ============================================================

st.markdown("# ✈️ TravelOps Client Intelligence Console")
st.caption(
    "AI-powered travel operations — verified client data plus "
    "Groq-powered assistants for support, trip planning, and travel advice."
)

choices = choice_lists()

tabs = st.tabs(
    [
        "📊 Overview",
        "✈️ Flight Search",
        "📋 Booking Tracking",
        "🏨 Hotel Search",
        "💳 Refund Control",
        "🤖 AI Support",
        "🗺️ Trip Planner",
        "🧭 Travel Advisor",
        "🔧 MCP Explorer",
    ]
)


# ------------------------------------------------------------
# OVERVIEW
# ------------------------------------------------------------
with tabs[0]:
    flights_df = st.session_state["flights"]
    bookings_df = st.session_state["bookings"]
    hotels_df = st.session_state["hotels"]

    available_flights = 0
    if not flights_df.empty and "status" in flights_df.columns:
        available_flights = len(
            flights_df[flights_df["status"].astype(str).str.lower().eq("available")]
        )

    kpis = [
        ("Flights", len(flights_df), "Client data", "✈"),
        ("Available", available_flights, "Flights", "✓"),
        ("Bookings", len(bookings_df), "Client data", "▦"),
        ("Hotels", len(hotels_df), "Client data", "⌂"),
        ("Refunds", len(st.session_state["refund_requests"]), "Pending", "↻"),
    ]

    kpi_html = "<div class='kpis'>" + "".join(
        f"""<div class='kpi'>
            <div class='kicon'>{icon}</div>
            <div>
                <small>{title}</small>
                <b>{value}</b>
                <span>{subtitle}</span>
            </div>
        </div>"""
        for title, value, subtitle, icon in kpis
    ) + "</div>"
    st.markdown(kpi_html, unsafe_allow_html=True)

    st.markdown("### Operational Alerts")
    for alert in get_operational_alerts():
        css_class = "alert-ok" if "No " in alert else "alert-warn"
        st.markdown(f"<div class='{css_class}'>{alert}</div>", unsafe_allow_html=True)

    if not flights_df.empty:
        st.markdown("### Flights preview")
        st.dataframe(flights_df.head(10), use_container_width=True)


# ------------------------------------------------------------
# FLIGHT SEARCH
# ------------------------------------------------------------
with tabs[1]:
    st.markdown("## ✈️ Flight Search")
    c1, c2 = st.columns(2)
    with c1:
        origin_sel = st.selectbox("Origin", [""] + choices["origins"], key="flight_origin")
    with c2:
        dest_sel = st.selectbox("Destination", [""] + choices["destinations"], key="flight_dest")

    if st.button("Search Flights", key="flight_search_btn"):
        try:
            df = search_flights(origin_sel, dest_sel, limit=50)
            st.markdown(f"**{len(df)} flight(s) found.**")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ {e}")


# ------------------------------------------------------------
# BOOKING TRACKING
# ------------------------------------------------------------
with tabs[2]:
    st.markdown("## 📋 Booking Tracking")
    booking_sel = st.selectbox(
        "Booking ID", [""] + choices["booking_ids"], key="booking_track_id"
    )

    if st.button("Track Booking", key="booking_track_btn"):
        if not booking_sel:
            st.markdown("<div class='error'>Please enter a Booking ID.</div>", unsafe_allow_html=True)
        else:
            try:
                d = get_booking_status(booking_sel)
                html = f"""
                <div class='detail'>
                    <small>{d['booking_id']}</small>
                    <h3>{d['customer_name']}</h3>
                    <span>{d['airline']} · {d['origin']} → {d['destination']}</span>
                    <div class='metrics'>
                        <div><small>Flight</small><b>{d['flight_id']}</b></div>
                        <div><small>Passengers</small><b>{d['passengers']}</b></div>
                        <div><small>Amount</small><b>${d['amount']:,.2f}</b></div>
                        <div><small>Status</small><b>{d['status']}</b></div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
                st.dataframe(pd.DataFrame([d]), use_container_width=True)
            except Exception as e:
                st.markdown(f"<div class='error'>❌ {e}</div>", unsafe_allow_html=True)


# ------------------------------------------------------------
# HOTEL SEARCH
# ------------------------------------------------------------
with tabs[3]:
    st.markdown("## 🏨 Hotel Search")
    city_sel = st.selectbox("City", [""] + choices["cities"], key="hotel_city")

    if st.button("Search Hotels", key="hotel_search_btn"):
        try:
            df = search_hotels(city=city_sel, limit=50)
            st.markdown(f"**{len(df)} hotel(s) found.**")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ {e}")


# ------------------------------------------------------------
# REFUND CONTROL
# ------------------------------------------------------------
with tabs[4]:
    st.markdown("## 💳 Refund Control")
    st.caption("Refund requests are always created as **Pending** and require human approval.")

    r1, r2 = st.columns([1, 2])
    with r1:
        refund_booking_sel = st.selectbox(
            "Booking ID", [""] + choices["booking_ids"], key="refund_booking_id"
        )
    with r2:
        refund_reason = st.text_input(
            "Reason", value="Customer cancellation", key="refund_reason"
        )

    if st.button("Submit Refund Request", key="refund_submit_btn"):
        try:
            d = create_refund_request(refund_booking_sel, refund_reason)
            html = f"""
            <div class='success'>
                <b>✓ Refund Request #{d['request_id']}</b><br><br>
                Booking: {d['booking_id']}<br>
                Amount: ${d['amount']:,.2f}<br>
                Reason: {d['reason']}<br><br>
                <small>Pending human approval</small>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<div class='error'>❌ {e}</div>", unsafe_allow_html=True)

    st.markdown("### All Refund Requests")
    st.dataframe(refund_table(), use_container_width=True)


# ------------------------------------------------------------
# AI SUPPORT ASSISTANT
# ------------------------------------------------------------
with tabs[5]:
    st.markdown("## 🤖 AI Support Assistant")
    st.caption("Verified booking data + uploaded policy, grounded through Groq.")

    support_booking_sel = st.selectbox(
        "Booking ID", [""] + choices["booking_ids"], key="support_booking_id"
    )
    support_issue = st.text_area(
        "Customer Question",
        value="Can I cancel my booking and get a refund?",
        height=120,
        key="support_issue",
    )

    if st.button("Generate Verified Response", key="support_btn"):
        answer, evidence = ai_support(support_booking_sel, support_issue)
        st.markdown(answer)
        if evidence:
            with st.expander("Show MCP Evidence"):
                st.markdown(evidence)


# ------------------------------------------------------------
# TRIP PLANNER
# ------------------------------------------------------------
with tabs[6]:
    st.markdown("## 🗺️ AI Trip Planner")
    st.caption("Groq AI creates the itinerary using verified client travel data.")

    t1, t2, t3 = st.columns(3)
    with t1:
        trip_dest_sel = st.selectbox(
            "Destination", [""] + choices["all_destinations"], key="trip_destination"
        )
    with t2:
        trip_dates_sel = st.selectbox("Travel Dates", [""] + choices["dates"], key="trip_dates")
    with t3:
        trip_budget = st.text_input("Budget", placeholder="$1000", key="trip_budget")

    if st.button("✨ Plan Trip", key="trip_btn"):
        answer, hotel_df = ai_trip_planner(trip_dest_sel, trip_dates_sel, trip_budget)
        st.markdown(answer)
        if not hotel_df.empty:
            st.dataframe(hotel_df, use_container_width=True)


# ------------------------------------------------------------
# TRAVEL ADVISOR
# ------------------------------------------------------------
with tabs[7]:
    st.markdown("## 🧭 AI Travel Advisor")
    st.caption("Recommendations based on destination, budget and preference.")

    a1, a2, a3 = st.columns(3)
    with a1:
        advisor_dest_sel = st.selectbox(
            "Destination", [""] + choices["all_destinations"], key="advisor_destination"
        )
    with a2:
        advisor_budget = st.text_input("Budget", placeholder="$1500", key="advisor_budget")
    with a3:
        advisor_pref_sel = st.selectbox(
            "Preference", [""] + choices["preferences"], key="advisor_preference"
        )

    if st.button("✨ Get Travel Advice", key="advisor_btn"):
        answer, hotel_df = ai_travel_advisor(advisor_dest_sel, advisor_budget, advisor_pref_sel)
        st.markdown(answer)
        if not hotel_df.empty:
            st.dataframe(hotel_df, use_container_width=True)


# ------------------------------------------------------------
# MCP EXPLORER
# ------------------------------------------------------------
with tabs[8]:
    st.markdown("## 🔧 Capability Explorer")
    st.caption(
        "The verified-data tools and AI prompt templates that power this console "
        "(equivalent to the original app's MCP tools/resources/prompts)."
    )

    explorer_rows = [
        {"Type": "Tool", "Name": "search_flights", "Description": "Search verified client flight inventory by origin/destination."},
        {"Type": "Tool", "Name": "search_hotels", "Description": "Search verified client hotel inventory by city/room type."},
        {"Type": "Tool", "Name": "get_booking_status", "Description": "Verify a booking and return its complete flight and customer information."},
        {"Type": "Tool", "Name": "create_refund_request", "Description": "Create a refund request. Never auto-approved — always requires human approval."},
        {"Type": "Tool", "Name": "get_operational_alerts", "Description": "Identify cancelled flights, pending bookings, and pending refunds from client data."},
        {"Type": "Resource", "Name": "travel://policy/cancellation", "Description": "Uploaded company cancellation policy text."},
        {"Type": "Resource", "Name": "travel://policy/refunds", "Description": "Uploaded company refund policy text."},
        {"Type": "Prompt", "Name": "Customer Support Assistant", "Description": "Grounds AI responses in verified booking data + uploaded policy."},
        {"Type": "Prompt", "Name": "Travel Advisor", "Description": "Produces destination/budget/preference-based advice grounded in verified hotel data."},
        {"Type": "Prompt", "Name": "Trip Planner", "Description": "Builds a day-by-day itinerary grounded in verified hotel data."},
        {"Type": "Prompt", "Name": "Operations Manager", "Description": "Summarizes critical issues, pending actions, and refunds needing approval."},
    ]
    st.dataframe(pd.DataFrame(explorer_rows), use_container_width=True)
