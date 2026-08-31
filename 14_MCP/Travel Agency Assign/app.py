"""
TravelOps Client Intelligence Console
Auto-converted from travel_agency_operation_mcp.ipynb for Hugging Face Spaces.
"""


# ===== CELL 0 =====
# ============================================================
# CELL 1 — INSTALL PACKAGES
# ============================================================


print("✅ Packages installed.")

# ===== CELL 1 =====
# ============================================================
# CELL 2 — IMPORTS
# ============================================================

import os
import json
import pandas as pd
import gradio as gr

from pydantic import BaseModel
from pypdf import PdfReader

from mcp import Client
from mcp.server.mcpserver import MCPServer

from groq import AsyncGroq

print("Gradio:", gr.__version__)
print("Pandas:", pd.__version__)
print("✅ Imports loaded.")

# ===== CELL 3 =====
# ============================================================
# CELL 3 — CLIENT WORKSPACE
# ============================================================

CLIENT_DATA = {
    "flights": pd.DataFrame(),
    "bookings": pd.DataFrame(),
    "hotels": pd.DataFrame(),
}

CLIENT_POLICY = ""

REFUND_REQUESTS = []


def clean_columns(df):

    df = df.copy()

    df.columns = [
        str(c)
        .strip()
        .lower()
        .replace(" ", "_")
        for c in df.columns
    ]

    return df


def read_required_sheet(excel_file, sheet_name):

    available = {
        str(s).strip().lower(): s
        for s in excel_file.sheet_names
    }

    key = sheet_name.strip().lower()

    if key not in available:

        raise ValueError(
            f"Missing Excel sheet: {sheet_name}. "
            f"Available sheets: {excel_file.sheet_names}"
        )

    return clean_columns(
        pd.read_excel(
            excel_file,
            sheet_name=available[key]
        )
    )


def load_client_workspace(excel_path, policy_path):

    global CLIENT_DATA
    global CLIENT_POLICY
    global REFUND_REQUESTS

    try:

        if not excel_path:

            return (
                "❌ Please upload the client's Excel file.",
                dashboard_html()
            )

        excel_file = pd.ExcelFile(excel_path)

        flights = read_required_sheet(
            excel_file,
            "Flights"
        )

        bookings = read_required_sheet(
            excel_file,
            "Bookings"
        )

        hotels = read_required_sheet(
            excel_file,
            "Hotels"
        )

        required_flights = {
            "flight_id",
            "airline",
            "origin",
            "destination",
            "departure",
            "arrival",
            "price",
            "seats",
            "status"
        }

        required_bookings = {
            "booking_id",
            "customer_name",
            "flight_id",
            "passengers",
            "status",
            "amount"
        }

        required_hotels = {
            "hotel_id",
            "name",
            "city",
            "room_type",
            "price_per_night",
            "rooms_available",
            "status"
        }

        missing_flights = (
            required_flights
            - set(flights.columns)
        )

        missing_bookings = (
            required_bookings
            - set(bookings.columns)
        )

        missing_hotels = (
            required_hotels
            - set(hotels.columns)
        )

        if missing_flights:

            raise ValueError(
                f"Flights sheet missing: "
                f"{sorted(missing_flights)}"
            )

        if missing_bookings:

            raise ValueError(
                f"Bookings sheet missing: "
                f"{sorted(missing_bookings)}"
            )

        if missing_hotels:

            raise ValueError(
                f"Hotels sheet missing: "
                f"{sorted(missing_hotels)}"
            )

        # ----------------------------------------------------
        # Read PDF policy
        # ----------------------------------------------------

        policy_text = ""

        if policy_path:

            reader = PdfReader(policy_path)

            pages = []

            for page in reader.pages:

                pages.append(
                    page.extract_text() or ""
                )

            policy_text = (
                "\n\n".join(pages)
                .strip()
            )

        # ----------------------------------------------------
        # Save client workspace
        # ----------------------------------------------------

        CLIENT_DATA["flights"] = flights
        CLIENT_DATA["bookings"] = bookings
        CLIENT_DATA["hotels"] = hotels

        CLIENT_POLICY = policy_text

        REFUND_REQUESTS = []

        return (
            f"""
## ✅ Client Workspace Loaded

| Data | Records |
|---|---:|
| Flights | {len(flights)} |
| Bookings | {len(bookings)} |
| Hotels | {len(hotels)} |
| Policy PDF | {"Loaded" if policy_text else "Not uploaded"} |

The dashboard and dropdowns have been updated using the client's data.
""",
            dashboard_html()
        )

    except Exception as e:

        return (
            f"""
## ❌ Upload Error

`{type(e).__name__}: {str(e)}`
""",
            dashboard_html()
        )


print("✅ Client workspace ready.")

# ===== CELL 5 =====
# ============================================================
# CELL 4 — DATA MODELS
# ============================================================

class FlightInfo(BaseModel):

    flight_id: str
    airline: str
    origin: str
    destination: str
    departure: str
    arrival: str
    price: float
    seats: int
    status: str


class BookingInfo(BaseModel):

    booking_id: str
    customer_name: str
    flight_id: str
    airline: str
    origin: str
    destination: str
    passengers: int
    status: str
    amount: float
    departure: str
    arrival: str


class HotelInfo(BaseModel):

    hotel_id: str
    name: str
    city: str
    room_type: str
    price_per_night: float
    rooms_available: int
    status: str


class RefundRequestResult(BaseModel):

    request_id: int
    booking_id: str
    amount: float
    reason: str
    status: str
    message: str


print("✅ Pydantic models ready.")

# ===== CELL 7 =====
# ============================================================
# CELL 5 — MCP SERVER
# ============================================================

mcp = MCPServer(
    "TravelOps Client MCP",
    instructions=(
        "Use verified client travel data. "
        "Never invent flights, bookings, hotels, "
        "prices, availability, or company policies. "
        "Refund requests require human approval."
    ),
)

print("✅ MCP server created.")

# ===== CELL 8 =====

# ============================================================
# CELL 1 — TRAVELOPS MCP CORE
# ============================================================

import pandas as pd
import json
from typing import Optional
from dataclasses import dataclass

from mcp.server import MCPServer


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    "TravelOps Client MCP",
    instructions=(
        "You are a Travel Operations MCP server. "
        "Use only verified client travel data. "
        "Never invent flights, hotels, bookings, prices, "
        "availability, refunds, or company policies. "
        "Refund requests require human approval."
    ),
)


# ============================================================
# CLIENT DATA
# ============================================================

CLIENT_DATA = {
    "flights": pd.DataFrame(),
    "bookings": pd.DataFrame(),
    "hotels": pd.DataFrame(),
}


# ============================================================
# REFUND REQUEST STORAGE
# ============================================================

REFUND_REQUESTS = []


# ============================================================
# BOOKING RESULT
# ============================================================

@dataclass
class BookingInfo:

    booking_id: str
    customer_name: str
    flight_id: str
    airline: str
    origin: str
    destination: str
    passengers: int
    status: str
    amount: float
    departure: str
    arrival: str


# ============================================================
# REFUND RESULT
# ============================================================

@dataclass
class RefundRequestResult:

    request_id: int
    booking_id: str
    amount: float
    reason: str
    status: str
    message: str


print("TravelOps MCP initialized successfully.")

# ===== CELL 11 =====

# ============================================================
# TOOL 1 — SEARCH FLIGHTS
# ============================================================

@mcp.tool(title="Search Flights")
def search_flights(
    origin: str = "",
    destination: str = "",
    limit: int = 20
) -> list[dict]:

    """
    Search verified client flight inventory.

    Filters:
    - origin
    - destination

    Returns only flights from uploaded client data.
    """

    df = CLIENT_DATA["flights"].copy()

    if df.empty:
        raise ValueError(
            "Client flight data has not been uploaded."
        )

    origin = (origin or "").strip().upper()
    destination = (destination or "").strip().upper()

    if origin:
        df = df[
            df["origin"]
            .astype(str)
            .str.upper()
            .str.contains(origin, na=False)
        ]

    if destination:
        df = df[
            df["destination"]
            .astype(str)
            .str.upper()
            .str.contains(destination, na=False)
        ]

    return df.head(limit).to_dict(
        orient="records"
    )

# ===== CELL 13 =====
# ============================================================
# TOOL 2 — GET FLIGHT DETAILS
# ============================================================

@mcp.tool(title="Get Flight Details")
def get_flight_details(
    flight_id: str
) -> dict:

    """
    Retrieve complete verified information
    for a specific flight.
    """

    df = CLIENT_DATA["flights"].copy()

    if df.empty:
        raise ValueError(
            "Client flight data has not been uploaded."
        )

    flight_id = (
        flight_id or ""
    ).strip().upper()

    df["_id"] = (
        df["flight_id"]
        .astype(str)
        .str.upper()
    )

    row = df[df["_id"] == flight_id]

    if row.empty:
        raise ValueError(
            f"Flight {flight_id} was not found."
        )

    return row.iloc[0].drop(
        labels=["_id"]
    ).to_dict()

# ===== CELL 15 =====
# ============================================================
# TOOL 3 — SEARCH HOTELS
# ============================================================

@mcp.tool(title="Search Hotels")
def search_hotels(
    city: str = "",
    room_type: str = "",
    limit: int = 20
) -> list[dict]:

    """
    Search verified client hotel inventory.
    """

    df = CLIENT_DATA["hotels"].copy()

    if df.empty:
        raise ValueError(
            "Client hotel data has not been uploaded."
        )

    city = (city or "").strip()
    room_type = (room_type or "").strip()

    if city:
        df = df[
            df["city"]
            .astype(str)
            .str.contains(
                city,
                case=False,
                na=False
            )
        ]

    if room_type:
        df = df[
            df["room_type"]
            .astype(str)
            .str.contains(
                room_type,
                case=False,
                na=False
            )
        ]

    return df.head(limit).to_dict(
        orient="records"
    )

# ===== CELL 17 =====

# ============================================================
# TOOL 4 — GET HOTEL DETAILS
# ============================================================

@mcp.tool(title="Get Hotel Details")
def get_hotel_details(
    hotel_id: str
) -> dict:

    """
    Retrieve complete verified information
    for a specific hotel.
    """

    df = CLIENT_DATA["hotels"].copy()

    if df.empty:
        raise ValueError(
            "Client hotel data has not been uploaded."
        )

    hotel_id = (
        hotel_id or ""
    ).strip().upper()

    df["_id"] = (
        df["hotel_id"]
        .astype(str)
        .str.upper()
    )

    row = df[df["_id"] == hotel_id]

    if row.empty:
        raise ValueError(
            f"Hotel {hotel_id} was not found."
        )

    return row.iloc[0].drop(
        labels=["_id"]
    ).to_dict()

# ===== CELL 19 =====
# ============================================================
# TOOL 5 — GET BOOKING STATUS
# ============================================================

@mcp.tool(title="Get Booking Status")
def get_booking_status(
    booking_id: str
) -> BookingInfo:

    """
    Verify a booking and return its complete
    flight and customer information.
    """

    bookings = CLIENT_DATA["bookings"].copy()
    flights = CLIENT_DATA["flights"].copy()

    if bookings.empty:
        raise ValueError(
            "Client booking data has not been uploaded."
        )

    booking_id = (
        booking_id or ""
    ).strip().upper()

    bookings["_id"] = (
        bookings["booking_id"]
        .astype(str)
        .str.upper()
    )

    row = bookings[
        bookings["_id"] == booking_id
    ]

    if row.empty:
        raise ValueError(
            f"Booking {booking_id} was not found."
        )

    booking = row.iloc[0]

    flights["_id"] = (
        flights["flight_id"]
        .astype(str)
        .str.upper()
    )

    flight_row = flights[
        flights["_id"]
        == str(
            booking["flight_id"]
        ).upper()
    ]

    if flight_row.empty:
        raise ValueError(
            f"Flight {booking['flight_id']} was not found."
        )

    flight = flight_row.iloc[0]

    return BookingInfo(
        booking_id=str(
            booking["booking_id"]
        ),
        customer_name=str(
            booking["customer_name"]
        ),
        flight_id=str(
            booking["flight_id"]
        ),
        airline=str(
            flight["airline"]
        ),
        origin=str(
            flight["origin"]
        ),
        destination=str(
            flight["destination"]
        ),
        passengers=int(
            booking["passengers"]
        ),
        status=str(
            booking["status"]
        ),
        amount=float(
            booking["amount"]
        ),
        departure=str(
            flight["departure"]
        ),
        arrival=str(
            flight["arrival"]
        ),
    )

# ===== CELL 21 =====
# ============================================================
# TOOL 7 — CREATE BOOKING REQUEST
# ============================================================

BOOKING_REQUESTS = []


@mcp.tool(title="Create Booking Request")
def create_booking_request(
    flight_id: str,
    customer_name: str,
    passengers: int = 1
) -> dict:

    """
    Create a booking request.

    This does NOT confirm a booking.
    It creates a request for human/agency processing.
    """

    flights = CLIENT_DATA["flights"].copy()

    if flights.empty:
        raise ValueError(
            "Client flight data has not been uploaded."
        )

    flight_id = (
        flight_id or ""
    ).strip().upper()

    flights["_id"] = (
        flights["flight_id"]
        .astype(str)
        .str.upper()
    )

    row = flights[
        flights["_id"] == flight_id
    ]

    if row.empty:
        raise ValueError(
            f"Flight {flight_id} was not found."
        )

    flight = row.iloc[0]

    request_id = (
        len(BOOKING_REQUESTS) + 1
    )

    request = {
        "request_id": request_id,
        "flight_id": str(
            flight["flight_id"]
        ),
        "customer_name": customer_name,
        "passengers": passengers,
        "status": "Pending",
    }

    BOOKING_REQUESTS.append(request)

    return {
        **request,
        "message": (
            "Booking request created. "
            "Final booking confirmation requires "
            "human/agency approval."
        )
    }

# ===== CELL 23 =====
# ============================================================
# TOOL 8 — CREATE REFUND REQUEST
# ============================================================

@mcp.tool(title="Create Refund Request")
def create_refund_request(
    booking_id: str,
    reason: str = "Customer cancellation"
) -> RefundRequestResult:

    """
    Create a refund request.

    Refunds are never automatically approved.
    Human approval is required.
    """

    booking = get_booking_status(
        booking_id
    )

    request_id = (
        len(REFUND_REQUESTS) + 1
    )

    request = {
        "request_id": request_id,
        "booking_id": booking.booking_id,
        "amount": booking.amount,
        "reason": reason,
        "status": "Pending",
    }

    REFUND_REQUESTS.append(request)

    return RefundRequestResult(
        request_id=request_id,
        booking_id=booking.booking_id,
        amount=booking.amount,
        reason=reason,
        status="Pending",
        message=(
            "Refund requires human approval."
        ),
    )

# ===== CELL 25 =====
# ============================================================
# TOOL 9 — GET REFUND STATUS
# ============================================================

@mcp.tool(title="Get Refund Status")
def get_refund_status(
    booking_id: str
) -> dict:

    """
    Retrieve the latest refund request
    associated with a booking.
    """

    booking_id = (
        booking_id or ""
    ).strip().upper()

    matches = [
        r
        for r in REFUND_REQUESTS
        if str(
            r["booking_id"]
        ).upper() == booking_id
    ]

    if not matches:
        raise ValueError(
            f"No refund request found for "
            f"booking {booking_id}."
        )

    return matches[-1]

# ===== CELL 27 =====
# ============================================================
# TOOL 10 — GET OPERATIONAL ALERTS
# ============================================================

@mcp.tool(title="Get Operational Alerts")
def get_operational_alerts() -> list[str]:

    """
    Identify important travel agency
    operational issues from client data.

    Examples:
    - cancelled flights
    - pending bookings
    - pending refunds
    - unavailable flights
    """

    alerts = []

    flights = CLIENT_DATA["flights"].copy()
    bookings = CLIENT_DATA["bookings"].copy()

    # --------------------------------------------------------
    # NO CLIENT DATA
    # --------------------------------------------------------

    if (
        flights.empty
        and bookings.empty
        and not REFUND_REQUESTS
    ):
        return [
            "No client travel data has been uploaded."
        ]

    # --------------------------------------------------------
    # FLIGHT ALERTS
    # --------------------------------------------------------

    if not flights.empty:

        if "status" in flights.columns:

            cancelled = flights[
                flights["status"]
                .astype(str)
                .str.lower()
                .eq("cancelled")
            ]

            if not cancelled.empty:

                alerts.append(
                    f"{len(cancelled)} "
                    "flight(s) are cancelled."
                )

            unavailable = flights[
                flights["status"]
                .astype(str)
                .str.lower()
                .isin(
                    [
                        "unavailable",
                        "sold out"
                    ]
                )
            ]

            if not unavailable.empty:

                alerts.append(
                    f"{len(unavailable)} "
                    "flight(s) are unavailable."
                )

    # --------------------------------------------------------
    # BOOKING ALERTS
    # --------------------------------------------------------

    if not bookings.empty:

        if "status" in bookings.columns:

            pending = bookings[
                bookings["status"]
                .astype(str)
                .str.lower()
                .eq("pending")
            ]

            if not pending.empty:

                alerts.append(
                    f"{len(pending)} "
                    "booking(s) are pending."
                )

    # --------------------------------------------------------
    # REFUND ALERTS
    # --------------------------------------------------------

    pending_refunds = [
        r
        for r in REFUND_REQUESTS
        if str(
            r["status"]
        ).lower() == "pending"
    ]

    if pending_refunds:

        alerts.append(
            f"{len(pending_refunds)} "
            "refund request(s) require human approval."
        )

    # --------------------------------------------------------
    # EVERYTHING OK
    # --------------------------------------------------------

    if not alerts:

        alerts.append(
            "No critical operational alerts detected."
        )

    return alerts

# ===== CELL 29 =====

# ============================================================
# RESOURCE 1 — CANCELLATION POLICY
# ============================================================

CLIENT_POLICY = ""


@mcp.resource(
    "travel://policy/cancellation"
)
def cancellation_policy():

    if not CLIENT_POLICY:

        return (
            "No client policy PDF has been uploaded."
        )

    return CLIENT_POLICY

# ===== CELL 30 =====
# ============================================================
# RESOURCE 2 — REFUND POLICY
# ============================================================

@mcp.resource(
    "travel://policy/refunds"
)
def refund_policy():

    if not CLIENT_POLICY:

        return (
            "No client policy PDF has been uploaded."
        )

    return CLIENT_POLICY

# ===== CELL 32 =====
# ============================================================
# PROMPT 1 — CUSTOMER SUPPORT
# ============================================================

@mcp.prompt(title="Customer Support Assistant")
def customer_support_response(
    issue: str,
    booking_id: str
):

    return f"""
You are a professional travel customer support assistant.

Booking ID:
{booking_id}

Customer issue:
{issue}

First verify the booking using MCP tools.

Use the uploaded company policy when
discussing cancellation or refunds.

Never invent:
- booking information
- prices
- availability
- refund amounts
- company policies

Refund approval must remain under human control.
""".strip()

# ===== CELL 34 =====
# ============================================================
# PROMPT 2 — TRAVEL ADVISOR
# ============================================================

@mcp.prompt(title="Travel Advisor")
def travel_advisor(
    destination: str,
    budget: str,
    preference: str
):

    return f"""
You are a professional travel advisor.

Destination:
{destination}

Budget:
{budget}

Traveler preference:
{preference}

Use verified TravelOps MCP data.

Clearly distinguish:

VERIFIED CLIENT DATA

from

AI RECOMMENDATIONS.

Never invent hotel prices,
hotel availability, flights,
bookings, or company policies.
""".strip()

# ===== CELL 36 =====
# ============================================================
# PROMPT 3 — TRIP PLANNER
# ============================================================

@mcp.prompt(title="Trip Planner")
def trip_planner(
    destination: str,
    dates: str,
    budget: str
):

    return f"""
You are a professional travel planner.

Destination:
{destination}

Travel dates:
{dates}

Budget:
{budget}

Use TravelOps MCP tools to obtain
verified hotel and travel information.

Create:

1. Recommended hotel
2. Day-by-day itinerary
3. Suggested activities
4. Budget considerations
5. Travel tips

Never invent availability or prices.

Clearly distinguish verified data
from recommendations.
""".strip()

# ===== CELL 38 =====

# ============================================================
# PROMPT 4 — OPERATIONS MANAGER
# ============================================================

@mcp.prompt(title="Operations Manager")
def operations_manager():

    return """
You are a Travel Operations Manager.

Use TravelOps MCP tools to review:

- flight problems
- booking problems
- refund requests
- operational alerts

Summarize:

1. Critical issues
2. Pending actions
3. Refunds requiring approval
4. Booking issues
5. Recommended management actions

Never invent operational information.
Use only verified client data.
""".strip()

# ===== CELL 40 =====
# ============================================================
# FINAL MCP TEST
# ============================================================

from mcp import Client


async def test_mcp():

    async with Client(mcp) as client:

        tools = await client.list_tools()

        resources = await client.list_resources()

        templates = await client.list_resource_templates()

        prompts = await client.list_prompts()

        print("\n==============================")
        print("TRAVELOPS MCP TOOLS")
        print("==============================")

        for tool in tools.tools:
            print("✓", tool.name)

        print("\n==============================")
        print("TRAVELOPS MCP RESOURCES")
        print("==============================")

        for resource in resources.resources:
            print("✓", resource.uri)

        print("\n==============================")
        print("TRAVELOPS MCP PROMPTS")
        print("==============================")

        for prompt in prompts.prompts:
            print("✓", prompt.name)

        print("\n==============================")
        print("MCP TEST COMPLETE")
        print("==============================")


# (interactive test skipped in deployed app)

# ===== CELL 42 =====
import os

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("⚠️  GROQ_API_KEY not set. AI features (Support Assistant, "
          "Trip Planner, Travel Advisor) will not work until it is "
          "configured as a Space secret.")

os.environ["GROQ_API_KEY"] = groq_api_key or ""

GROQ_MODEL = "openai/gpt-oss-20b"

print("Groq configured." if groq_api_key else "Groq NOT configured (missing secret).")

# ===== CELL 43 =====
import os
import json
import pandas as pd
import gradio as gr

from groq import AsyncGroq
from mcp import Client

# ===== CELL 44 =====
# (duplicate Groq key setup from notebook removed; handled above)

# ===== CELL 45 =====
groq_client = AsyncGroq(api_key=groq_api_key) if groq_api_key else None

print("Groq client ready." if groq_client else "Groq client not created (no API key).")

# ===== CELL 46 =====
CLIENT_DATA = {
    "flights": pd.DataFrame(),
    "bookings": pd.DataFrame(),
    "hotels": pd.DataFrame()
}

CLIENT_POLICY = ""

REFUND_REQUESTS = []

print("Empty client workspace created.")

# ===== CELL 47 =====
def unwrap_mcp(value):

    if value is None:
        return None

    if isinstance(value, dict):

        for key in [
            "result",
            "results",
            "items",
            "data"
        ]:

            if (
                key in value
                and len(value) == 1
                and isinstance(
                    value[key],
                    (list, tuple)
                )
            ):
                return value[key]

        if (
            "result" in value
            and len(value) == 1
            and isinstance(
                value["result"],
                dict
            )
        ):
            return value["result"]

    return value


def to_df(value):

    value = unwrap_mcp(value)

    if isinstance(value, pd.DataFrame):
        return value.copy()

    if isinstance(value, list):

        if not value:
            return pd.DataFrame()

        if all(
            isinstance(x, dict)
            for x in value
        ):
            return pd.DataFrame(value)

        return pd.DataFrame(
            {"value": value}
        )

    if isinstance(value, dict):
        return pd.DataFrame([value])

    return pd.DataFrame()

# ===== CELL 49 =====
def unwrap_mcp(value):

    if value is None:
        return None

    if isinstance(value, dict):

        for key in [
            "result",
            "results",
            "items",
            "data"
        ]:

            if (
                key in value
                and len(value) == 1
                and isinstance(
                    value[key],
                    (list, tuple)
                )
            ):
                return value[key]

        if (
            "result" in value
            and len(value) == 1
            and isinstance(
                value["result"],
                dict
            )
        ):
            return value["result"]

    return value


def to_df(value):

    value = unwrap_mcp(value)

    if isinstance(value, pd.DataFrame):
        return value.copy()

    if isinstance(value, list):

        if not value:
            return pd.DataFrame()

        if all(
            isinstance(x, dict)
            for x in value
        ):
            return pd.DataFrame(value)

        return pd.DataFrame(
            {"value": value}
        )

    if isinstance(value, dict):
        return pd.DataFrame([value])

    return pd.DataFrame()

# ===== CELL 51 =====

def load_client_workspace(
    excel_path,
    policy_path
):

    global CLIENT_DATA
    global CLIENT_POLICY
    global REFUND_REQUESTS

    if not excel_path:
        return (
            "❌ Please upload the client's Excel file first.",
            dashboard_html()
        )

    try:

        excel = pd.ExcelFile(excel_path)

        sheets = excel.sheet_names

        flights = pd.DataFrame()
        bookings = pd.DataFrame()
        hotels = pd.DataFrame()

        for sheet in sheets:

            df = pd.read_excel(
                excel_path,
                sheet_name=sheet
            )

            name = sheet.lower().strip()

            if "flight" in name:
                flights = df

            elif "booking" in name:
                bookings = df

            elif "hotel" in name:
                hotels = df

        CLIENT_DATA = {
            "flights": flights,
            "bookings": bookings,
            "hotels": hotels
        }

        REFUND_REQUESTS = []

        if policy_path:

            with open(
                policy_path,
                "rb"
            ) as f:

                pdf_bytes = f.read()

            # Store PDF text if your MCP server already
            # has its own PDF extraction logic, replace
            # this section with that logic.

            try:

                from pypdf import PdfReader

                reader = PdfReader(
                    policy_path
                )

                CLIENT_POLICY = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

            except Exception:

                CLIENT_POLICY = (
                    "Policy PDF uploaded, "
                    "but text extraction failed."
                )

        else:

            CLIENT_POLICY = ""

        return (
            f"""
### ✅ Client Workspace Loaded

- Flights: **{len(flights)}**
- Bookings: **{len(bookings)}**
- Hotels: **{len(hotels)}**
- Policy: **{"Uploaded" if CLIENT_POLICY else "Not uploaded"}**
            """,
            dashboard_html()
        )

    except Exception as e:

        return (
            f"❌ Workspace loading failed: "
            f"`{type(e).__name__}: {e}`",
            dashboard_html()
        )

# ===== CELL 53 =====

def dashboard_html():

    flights = len(
        CLIENT_DATA["flights"]
    )

    bookings = len(
        CLIENT_DATA["bookings"]
    )

    hotels = len(
        CLIENT_DATA["hotels"]
    )

    available_flights = 0

    if (
        not CLIENT_DATA["flights"].empty
        and "status" in CLIENT_DATA["flights"].columns
    ):

        available_flights = len(
            CLIENT_DATA["flights"][
                CLIENT_DATA["flights"]["status"]
                .astype(str)
                .str.lower()
                .eq("available")
            ]
        )

    pending_refunds = len(
        REFUND_REQUESTS
    )

    values = [
        ("Flights", flights, "Client data", "✈"),
        (
            "Available",
            available_flights,
            "Flights",
            "✓"
        ),
        (
            "Bookings",
            bookings,
            "Client data",
            "▦"
        ),
        (
            "Hotels",
            hotels,
            "Client data",
            "⌂"
        ),
        (
            "Refunds",
            pending_refunds,
            "Pending",
            "↻"
        )
    ]

    return (
        "<div class='kpis'>"
        +
        "".join(
            f"""
            <div class='kpi'>
                <div class='kicon'>{icon}</div>

                <div>
                    <small>{title}</small>
                    <b>{value}</b>
                    <span>{subtitle}</span>
                </div>
            </div>
            """
            for title, value, subtitle, icon
            in values
        )
        +
        "</div>"
    )

# ===== CELL 55 =====
def get_dropdown_updates():

    flights = CLIENT_DATA["flights"]
    bookings = CLIENT_DATA["bookings"]
    hotels = CLIENT_DATA["hotels"]

    # -------------------------
    # FLIGHTS
    # -------------------------

    if not flights.empty:

        origins = sorted(
            flights["origin"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        destinations = sorted(
            flights["destination"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        dates = sorted(
            pd.to_datetime(
                flights["departure"],
                errors="coerce"
            )
            .dropna()
            .dt.strftime("%Y-%m-%d")
            .unique()
            .tolist()
        )

    else:

        origins = []
        destinations = []
        dates = []

    # -------------------------
    # BOOKINGS
    # -------------------------

    if not bookings.empty:

        booking_ids = sorted(
            bookings["booking_id"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

    else:

        booking_ids = []

    # -------------------------
    # HOTELS
    # -------------------------

    if not hotels.empty:

        cities = sorted(
            hotels["city"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

    else:

        cities = []

    all_destinations = sorted(
        set(
            destinations + cities
        )
    )

    preferences = [
        "Luxury",
        "Budget",
        "Family",
        "Business",
        "Beach",
        "Convenient location"
    ]

    return (

        gr.Dropdown(
            choices=origins,
            value=None,
            label="Origin",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=destinations,
            value=None,
            label="Destination",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=booking_ids,
            value=None,
            label="Booking ID",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=cities,
            value=None,
            label="City",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=all_destinations,
            value=None,
            label="Destination",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=dates,
            value=None,
            label="Travel Dates",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=all_destinations,
            value=None,
            label="Destination",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=preferences,
            value=None,
            label="Preference",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=booking_ids,
            value=None,
            label="Booking ID",
            allow_custom_value=True
        ),

        gr.Dropdown(
            choices=booking_ids,
            value=None,
            label="Booking ID",
            allow_custom_value=True
        )
    )

# ===== CELL 57 =====
async def ui_search_flights(
    origin,
    destination
):

    try:

        async with Client(mcp) as c:

            result = await c.call_tool(
                "search_flights",
                {
                    "origin": origin or "",
                    "destination": destination or "",
                    "limit": 50
                }
            )

        if result.is_error:

            msg = (
                result.content[0].text
                if result.content
                else "Flight search failed."
            )

            return (
                pd.DataFrame(),
                f"⚠️ {msg}"
            )

        df = to_df(
            result.structured_content
        )

        return (
            df,
            f"**{len(df)} flight(s) found.**"
        )

    except Exception as e:

        return (
            pd.DataFrame(),
            f"❌ {type(e).__name__}: {e}"
        )

# ===== CELL 59 =====
async def ui_booking(
    booking_id
):

    if not booking_id:

        return (
            "<div class='error'>"
            "Please enter a Booking ID."
            "</div>",
            pd.DataFrame()
        )

    try:

        async with Client(mcp) as c:

            result = await c.call_tool(
                "get_booking_status",
                {
                    "booking_id":
                    str(booking_id).strip().upper()
                }
            )

        if result.is_error:

            return (
                "<div class='error'>"
                "Booking not found."
                "</div>",
                pd.DataFrame()
            )

        d = result.structured_content

        html = f"""
        <div class='detail'>

            <small>
                {d['booking_id']}
            </small>

            <h3>
                {d['customer_name']}
            </h3>

            <span>
                {d['airline']}
                ·
                {d['origin']} →
                {d['destination']}
            </span>

            <div class='metrics'>

                <div>
                    <small>Flight</small>
                    <b>{d['flight_id']}</b>
                </div>

                <div>
                    <small>Passengers</small>
                    <b>{d['passengers']}</b>
                </div>

                <div>
                    <small>Amount</small>
                    <b>${d['amount']:,.2f}</b>
                </div>

                <div>
                    <small>Status</small>
                    <b>{d['status']}</b>
                </div>

            </div>

        </div>
        """

        return (
            html,
            to_df(d)
        )

    except Exception as e:

        return (
            f"""
            <div class='error'>
            ❌ {type(e).__name__}: {e}
            </div>
            """,
            pd.DataFrame()
        )

# ===== CELL 61 =====

async def ui_hotels(city):

    try:

        async with Client(mcp) as c:

            result = await c.call_tool(
                "search_hotels",
                {
                    "city": city or "",
                    "room_type": "",
                    "limit": 50
                }
            )

        if result.is_error:

            msg = (
                result.content[0].text
                if result.content
                else "Hotel search failed."
            )

            return (
                pd.DataFrame(),
                f"⚠️ {msg}"
            )

        df = to_df(
            result.structured_content
        )

        return (
            df,
            f"**{len(df)} hotel(s) found.**"
        )

    except Exception as e:

        return (
            pd.DataFrame(),
            f"❌ {type(e).__name__}: {e}"
        )

# ===== CELL 63 =====

def refund_table():

    if not REFUND_REQUESTS:

        return pd.DataFrame(
            columns=[
                "request_id",
                "booking_id",
                "amount",
                "reason",
                "status"
            ]
        )

    return pd.DataFrame(
        REFUND_REQUESTS
    )

# ===== CELL 65 =====

async def ui_refund(
    booking_id,
    reason
):

    try:

        async with Client(mcp) as c:

            result = await c.call_tool(
                "create_refund_request",
                {
                    "booking_id":
                    str(booking_id or "")
                    .strip()
                    .upper(),

                    "reason":
                    reason or
                    "Customer cancellation"
                }
            )

        if result.is_error:

            return (
                "<div class='error'>"
                "Refund request failed."
                "</div>",
                refund_table()
            )

        d = result.structured_content

        message = f"""
        <div class='success'>

            <b>
                ✓ Refund Request #{d['request_id']}
            </b>

            <br><br>

            Booking:
            {d['booking_id']}

            <br>

            Amount:
            ${d['amount']:,.2f}

            <br>

            Reason:
            {d['reason']}

            <br><br>

            <small>
                Pending human approval
            </small>

        </div>
        """

        return (
            message,
            refund_table()
        )

    except Exception as e:

        return (
            f"""
            <div class='error'>
                ❌ {type(e).__name__}: {e}
            </div>
            """,
            refund_table()
        )

# ===== CELL 67 =====
async def ui_support(
    booking_id,
    issue
):

    if not booking_id:

        return (
            "❌ Please enter a Booking ID.",
            ""
        )

    if not issue:

        return (
            "❌ Please enter the customer's question.",
            ""
        )

    if groq_client is None:

        return (
            "❌ GROQ_API_KEY is not configured for this Space. "
            "Add it under Settings → Repository secrets.",
            ""
        )

    try:

        async with Client(mcp) as c:

            booking = await c.call_tool(
                "get_booking_status",
                {
                    "booking_id":
                    str(booking_id)
                    .strip()
                    .upper()
                }
            )

            policy = await c.read_resource(
                "travel://policy/cancellation"
            )

            refund_policy = await c.read_resource(
                "travel://policy/refunds"
            )

        if booking.is_error:

            return (
                "❌ Booking could not be verified.",
                ""
            )

        d = booking.structured_content

        policy_text = "\n".join(
            x.text
            for x in policy.contents
            if hasattr(x, "text")
        )

        refund_text = "\n".join(
            x.text
            for x in refund_policy.contents
            if hasattr(x, "text")
        )

        prompt = f"""
You are a professional travel customer support AI.

Your job is to help a travel company's customer support team.

VERIFIED BOOKING DATA:
{json.dumps(d, indent=2)}

CUSTOMER QUESTION:
{issue}

COMPANY CANCELLATION POLICY:
{policy_text}

COMPANY REFUND POLICY:
{refund_text}

Instructions:

1. Use the verified booking data.
2. Use only the provided company policies for
   cancellation and refund decisions.
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

        response = await groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are a professional travel "
                    "customer support AI."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.3,

            max_completion_tokens=1500
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        evidence = (
            "### Verified Booking\n\n"
            "```json\n"
            +
            json.dumps(
                d,
                indent=2
            )
            +
            "\n```\n\n"
            "### Cancellation Policy\n\n"
            +
            policy_text
            +
            "\n\n### Refund Policy\n\n"
            +
            refund_text
        )

        return (
            answer,
            evidence
        )

    except Exception as e:

        return (
            f"❌ Support AI Error\n\n"
            f"`{type(e).__name__}: {e}`",
            ""
        )

# ===== CELL 69 =====
async def ui_trip_planner(
    destination,
    dates,
    budget
):

    if not destination:

        return (
            "❌ Please select a destination.",
            pd.DataFrame()
        )

    if groq_client is None:

        return (
            "❌ GROQ_API_KEY is not configured for this Space. "
            "Add it under Settings → Repository secrets.",
            pd.DataFrame()
        )

    try:

        async with Client(mcp) as c:

            hotels = await c.call_tool(
                "search_hotels",
                {
                    "city": destination,
                    "room_type": "",
                    "limit": 20
                }
            )

        if hotels.is_error:

            msg = (
                hotels.content[0].text
                if hotels.content
                else "Hotel search failed."
            )

            return (
                f"⚠️ {msg}",
                pd.DataFrame()
            )

        hotel_df = to_df(
            hotels.structured_content
        )

        hotel_data = (
            hotel_df
            .to_dict(
                orient="records"
            )
            if not hotel_df.empty
            else []
        )

        prompt = f"""
You are an AI travel planning assistant
for a professional travel agency.

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
- Never claim a hotel is available unless
  it appears in the verified data.
- If hotel data is empty, clearly say that
  no client hotel data was found.
- General activities may be recommendations,
  but label them as recommendations.
"""

        response = await groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are an expert AI travel planner."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.5,

            max_completion_tokens=1800
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        return (
            answer,
            hotel_df
        )

    except Exception as e:

        return (
            f"""
            ❌ Trip Planner Error

            `{type(e).__name__}: {e}`
            """,
            pd.DataFrame()
        )

# ===== CELL 71 =====
async def ui_travel_advisor(
    destination,
    budget,
    preference
):

    if not destination:

        return (
            "❌ Please select a destination.",
            pd.DataFrame()
        )

    if groq_client is None:

        return (
            "❌ GROQ_API_KEY is not configured for this Space. "
            "Add it under Settings → Repository secrets.",
            pd.DataFrame()
        )

    try:

        async with Client(mcp) as c:

            hotels = await c.call_tool(
                "search_hotels",
                {
                    "city": destination,
                    "room_type": "",
                    "limit": 20
                }
            )

        if hotels.is_error:

            msg = (
                hotels.content[0].text
                if hotels.content
                else "Hotel search failed."
            )

            return (
                f"⚠️ {msg}",
                pd.DataFrame()
            )

        hotel_df = to_df(
            hotels.structured_content
        )

        hotel_data = (
            hotel_df
            .to_dict(
                orient="records"
            )
            if not hotel_df.empty
            else []
        )

        prompt = f"""
You are an AI travel advisor working
for a professional travel agency.

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
- Clearly distinguish verified information
  from general recommendations.
"""

        response = await groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are an expert AI travel advisor."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.5,

            max_completion_tokens=1800
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        return (
            answer,
            hotel_df
        )

    except Exception as e:

        return (
            f"""
            ❌ Travel Advisor Error

            `{type(e).__name__}: {e}`
            """,
            pd.DataFrame()
        )

# ===== CELL 73 =====
async def ui_explorer():

    try:

        async with Client(mcp) as c:

            tools = await c.list_tools()

            resources = await c.list_resources()

            templates = (
                await c.list_resource_templates()
            )

            prompts = await c.list_prompts()

        rows = []

        for x in tools.tools:

            rows.append({
                "Type": "Tool",
                "Name": x.name,
                "Description":
                    x.description or ""
            })

        for x in resources.resources:

            rows.append({
                "Type": "Resource",
                "Name": str(x.uri),
                "Description":
                    getattr(
                        x,
                        "description",
                        ""
                    ) or ""
            })

        for x in templates.resource_templates:

            rows.append({
                "Type":
                    "Resource Template",
                "Name":
                    str(x.uri_template),
                "Description":
                    getattr(
                        x,
                        "description",
                        ""
                    ) or ""
            })

        for x in prompts.prompts:

            rows.append({
                "Type": "Prompt",
                "Name": x.name,
                "Description":
                    x.description or ""
            })

        return pd.DataFrame(rows)

    except Exception as e:

        return pd.DataFrame([
            {
                "Type": "ERROR",
                "Name": type(e).__name__,
                "Description": str(e)
            }
        ])

# ===== CELL 75 =====
CSS = """

.gradio-container {
    max-width: 1500px !important;
    margin: auto !important;

    background:
        linear-gradient(
            135deg,
            #ffffff,
            #faf5ff,
            #fff5fa
        ) !important;
}

.kpis {
    display: grid !important;
    grid-template-columns:
        repeat(5, 1fr) !important;

    gap: 14px !important;
    margin-bottom: 20px !important;
}

.kpi {
    background: white !important;
    border: 1px solid #ddc7ef !important;
    border-radius: 20px !important;
    padding: 18px !important;

    box-shadow:
        0 10px 28px
        rgba(124,58,237,.09) !important;
}

.kpi small {
    display: block !important;
    color: #6b4d7d !important;
}

.kpi b {
    display: block !important;
    color: #291039 !important;
    font-size: 25px !important;
}

.kpi span {
    color: #694e79 !important;
}

.kicon {
    font-size: 25px !important;
    color: #7e22ce !important;
}

.detail {
    background: white !important;
    border: 1px solid #dfc9f4 !important;
    border-radius: 20px !important;
    padding: 22px !important;
}

.metrics {
    display: grid !important;
    grid-template-columns:
        repeat(4, 1fr) !important;

    gap: 12px !important;
    margin-top: 20px !important;
}

.metrics div {
    background: #fcf9ff !important;
    border: 1px solid #eadcff !important;
    border-radius: 12px !important;
    padding: 14px !important;
}

.metrics small {
    display: block !important;
}

.metrics b {
    display: block !important;
    margin-top: 5px !important;
}

.error {
    background: #fff1f7 !important;
    color: #9f1239 !important;
    border: 1px solid #f9c8df !important;
    border-radius: 15px !important;
    padding: 16px !important;
}

.success {
    background: #f7efff !important;
    color: #6b21a8 !important;
    border: 1px solid #dfc4fb !important;
    border-radius: 15px !important;
    padding: 16px !important;
}

@media (max-width: 700px) {

    .kpis {
        grid-template-columns:
            repeat(2, 1fr) !important;
    }

    .metrics {
        grid-template-columns:
            repeat(2, 1fr) !important;
    }
}

footer {
    display: none !important;
}

"""

# ===== CELL 77 =====
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate"
)

with gr.Blocks(
    title="TravelOps Client Intelligence Console"
) as demo:

    # ========================================================
    # HEADER
    # ========================================================

    gr.Markdown(
        """
        # ✈️ TravelOps Client Intelligence Console

        **AI-powered travel operations platform for client-specific
        data, customer support, planning and decision-making.**

        Upload a client's Excel data and company policy,
        then use the operational tools and AI assistants.
        """
    )

    # ========================================================
    # DASHBOARD
    # ========================================================

    dashboard = gr.HTML(
        value=dashboard_html()
    )

    # ========================================================
    # TABS
    # ========================================================

    with gr.Tabs():

        # ----------------------------------------------------
        # CLIENT SETUP
        # ----------------------------------------------------

        with gr.Tab("Client Setup"):

            gr.Markdown(
                """
                ## Client Workspace

                Upload the client's operational data and
                company policy.
                """
            )

            with gr.Row():

                client_excel = gr.File(
                    label="Client Excel",
                    file_types=[
                        ".xlsx",
                        ".xls"
                    ],
                    type="filepath"
                )

                client_policy = gr.File(
                    label="Company Policy PDF",
                    file_types=[".pdf"],
                    type="filepath"
                )

            load_client_btn = gr.Button(
                "Load Client Workspace",
                variant="primary"
            )

            client_status = gr.Markdown(
                "No client data loaded."
            )

        # ----------------------------------------------------
        # OVERVIEW
        # ----------------------------------------------------

        with gr.Tab("Overview"):

            gr.Markdown(
                """
                ## 📊 Operations Overview

                Monitor the current client workspace.
                """

            )

            refresh = gr.Button(
                "↻ Refresh Dashboard"
            )

        # ----------------------------------------------------
        # FLIGHTS
        # ----------------------------------------------------

        with gr.Tab("Flight Search"):

            gr.Markdown(
                """
                ## ✈️ Flight Search

                Search verified flights from the client's
                uploaded travel data.
                """
            )

            with gr.Row():

                origin = gr.Dropdown(
                    choices=[],
                    label="Origin",
                    allow_custom_value=True
                )

                destination = gr.Dropdown(
                    choices=[],
                    label="Destination",
                    allow_custom_value=True
                )

            flight_btn = gr.Button(
                "Search Flights",
                variant="primary"
            )

            flight_msg = gr.Markdown()

            flight_df = gr.Dataframe(
                interactive=False,
                wrap=True
            )

        # ----------------------------------------------------
        # BOOKING
        # ----------------------------------------------------

        with gr.Tab("Booking Tracking"):

            gr.Markdown(
                """
                ## 🎫 Booking Tracking

                Verify a customer's booking through MCP.
                """
            )

            with gr.Row():

                booking_id = gr.Dropdown(
                    choices=[],
                    label="Booking ID",
                    allow_custom_value=True
                )

                booking_btn = gr.Button(
                    "Check Booking",
                    variant="primary"
                )

            booking_card = gr.HTML(
                "<div class='detail'>"
                "Enter a Booking ID."
                "</div>"
            )

            booking_raw = gr.Dataframe(
                label="Verified Booking Data",
                interactive=False
            )

        # ----------------------------------------------------
        # HOTEL
        # ----------------------------------------------------

        with gr.Tab("Hotel Search"):

            gr.Markdown(
                """
                ## 🏨 Hotel Search

                Search verified client hotel information.
                """
            )

            hotel_city = gr.Dropdown(
                choices=[],
                label="City",
                allow_custom_value=True
            )

            hotel_btn = gr.Button(
                "Search Hotels",
                variant="primary"
            )

            hotel_msg = gr.Markdown()

            hotel_df = gr.Dataframe(
                interactive=False,
                wrap=True
            )

        # ----------------------------------------------------
        # REFUND
        # ----------------------------------------------------

        with gr.Tab("Refund Control"):

            gr.Markdown(
                """
                ## 💰 Refund Control

                Refund requests are created as **Pending**
                and require human approval.
                """
            )

            refund_booking = gr.Dropdown(
                choices=[],
                label="Booking ID",
                allow_custom_value=True
            )

            refund_reason = gr.Textbox(
                label="Refund Reason",
                value="Customer cancellation",
                lines=3
            )

            refund_btn = gr.Button(
                "Create Refund Request",
                variant="primary"
            )

            refund_status = gr.HTML(
                "<div class='detail'>"
                "No refund request created."
                "</div>"
            )

            refund_df = gr.Dataframe(
                value=refund_table(),
                label="Refund Register",
                interactive=False,
                wrap=True
            )

        # ----------------------------------------------------
        # SUPPORT
        # ----------------------------------------------------

        with gr.Tab("Support Assistant"):

            gr.Markdown(
                """
                ## 🤖 AI Customer Support Assistant

                Combines:

                **Booking Verification + Company Policy + Groq AI**
                """
            )

            support_booking = gr.Dropdown(
                choices=[],
                label="Booking ID",
                allow_custom_value=True
            )

            issue = gr.Textbox(
                label="Customer Question",
                value=(
                    "Can I cancel my booking "
                    "and get a refund?"
                ),
                lines=5
            )

            support_btn = gr.Button(
                "Generate Verified Response",
                variant="primary"
            )

            support_answer = gr.Markdown(
                "AI response will appear here."
            )

            with gr.Accordion(
                "Show MCP Evidence",
                open=False
            ):

                support_evidence = gr.Markdown()

        # ----------------------------------------------------
        # TRIP PLANNER
        # ----------------------------------------------------

        with gr.Tab("Trip Planner"):

            gr.Markdown(
                """
                ## 🗺️ AI Trip Planner

                Uses client hotel data + Groq AI to
                create a personalized travel plan.
                """
            )

            trip_destination = gr.Dropdown(
                choices=[],
                label="Destination",
                allow_custom_value=True
            )

            trip_dates = gr.Dropdown(
                choices=[],
                label="Travel Dates",
                allow_custom_value=True
            )

            trip_budget = gr.Textbox(
                label="Budget",
                placeholder="$1000"
            )

            trip_btn = gr.Button(
                "Plan Trip",
                variant="primary"
            )

            trip_result = gr.Markdown(
                "Your AI travel plan will appear here."
            )

            trip_hotels = gr.Dataframe(
                interactive=False,
                wrap=True
            )

        # ----------------------------------------------------
        # ADVISOR
        # ----------------------------------------------------

        with gr.Tab("Travel Advisor"):

            gr.Markdown(
                """
                ## 🧭 AI Travel Advisor

                Get personalized travel recommendations
                based on destination, budget and preference.
                """
            )

            advisor_destination = gr.Dropdown(
                choices=[],
                label="Destination",
                allow_custom_value=True
            )

            advisor_budget = gr.Textbox(
                label="Budget",
                placeholder="$1500"
            )

            advisor_preference = gr.Dropdown(
                choices=[
                    "Luxury",
                    "Budget",
                    "Family",
                    "Business",
                    "Beach",
                    "Convenient location"
                ],
                label="Preference",
                allow_custom_value=True
            )

            advisor_btn = gr.Button(
                "Get Travel Advice",
                variant="primary"
            )

            advisor_result = gr.Markdown(
                "AI travel advice will appear here."
            )

            advisor_hotels = gr.Dataframe(
                interactive=False,
                wrap=True
            )

        # ----------------------------------------------------
        # MCP EXPLORER
        # ----------------------------------------------------

        with gr.Tab("MCP Explorer"):

            gr.Markdown(
                """
                ## 🔌 MCP Capability Explorer

                View the tools, resources,
                resource templates and prompts
                exposed by the MCP server.
                """
            )

            explorer_btn = gr.Button(
                "Discover MCP Capabilities",
                variant="primary"
            )

            explorer_df = gr.Dataframe(
                interactive=False,
                wrap=True
            )

# ===== CELL 79 =====
# ============================================================
# TRAVELOPS CLIENT INTELLIGENCE CONSOLE
# COMPLETE GRADIO UI + EVENTS
# ============================================================

import gradio as gr


# ============================================================
# THEME
# ============================================================

theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate"
)


# ============================================================
# CSS
# ============================================================

CSS = """

.gradio-container {
    max-width: 1500px !important;
    margin: auto !important;

    background:
        radial-gradient(
            circle at 8% 2%,
            rgba(168, 85, 247, .16),
            transparent 28%
        ),
        radial-gradient(
            circle at 92% 2%,
            rgba(236, 72, 153, .14),
            transparent 28%
        ),
        linear-gradient(
            135deg,
            #ffffff 0%,
            #faf5ff 50%,
            #fff5fa 100%
        ) !important;

    color: #24132f !important;
}


/* HERO */

.hero {
    padding: 38px !important;
    border-radius: 28px !important;
    margin-bottom: 20px !important;

    background:
        radial-gradient(
            circle at 85% 15%,
            rgba(244,114,182,.35),
            transparent 24%
        ),
        linear-gradient(
            135deg,
            #4c1d95 0%,
            #7e22ce 48%,
            #be185d 100%
        ) !important;

    box-shadow:
        0 18px 45px
        rgba(91,33,182,.20) !important;
}

.hero h1,
.hero p,
.hero span {
    color: #ffffff !important;
}

.hero h1 {
    font-size: 40px !important;
    font-weight: 800 !important;
}

.hero p {
    color: #fce7f3 !important;
    line-height: 1.7 !important;
}

.badge {
    display: inline-block !important;
    padding: 8px 14px !important;
    border-radius: 999px !important;
    background: rgba(255,255,255,.14) !important;
    border: 1px solid rgba(255,255,255,.25) !important;
}

.chips {
    display: flex !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    margin-top: 18px !important;
}

.chips span {
    color: #ffffff !important;
    background: rgba(255,255,255,.13) !important;
    border: 1px solid rgba(255,255,255,.18) !important;
    padding: 7px 11px !important;
    border-radius: 999px !important;
}


/* KPI */

.kpis {
    display: grid !important;
    grid-template-columns: repeat(5,1fr) !important;
    gap: 14px !important;
    margin-bottom: 20px !important;
}

.kpi {
    background: #ffffff !important;
    border: 1px solid #ddc7ef !important;
    border-radius: 20px !important;
    padding: 18px !important;

    display: flex !important;
    gap: 13px !important;
    align-items: center !important;

    box-shadow:
        0 10px 28px rgba(124,58,237,.09) !important;
}

.kpi small {
    display: block !important;
    color: #5e4470 !important;
    font-weight: 700 !important;
}

.kpi b {
    display: block !important;
    color: #291039 !important;
    font-size: 23px !important;
    font-weight: 800 !important;
}

.kpi span {
    display: block !important;
    color: #694e79 !important;
    font-size: 11px !important;
}

.kicon {
    width: 44px !important;
    height: 44px !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    border-radius: 14px !important;

    background:
        linear-gradient(
            135deg,
            #f3e8ff,
            #fce7f3
        ) !important;

    color: #7e22ce !important;
    font-size: 20px !important;
}


/* CARD */

.detail {
    background: #ffffff !important;
    color: #24132f !important;

    border: 1px solid #dfc9f4 !important;
    border-radius: 22px !important;
    padding: 22px !important;

    box-shadow:
        0 10px 30px rgba(124,58,237,.07) !important;
}

.detail h3 {
    color: #38164f !important;
}

.detail small {
    color: #8b21a8 !important;
}

.detail span {
    color: #644775 !important;
}


/* METRICS */

.metrics {
    display: grid !important;
    grid-template-columns: repeat(4,1fr) !important;
    gap: 11px !important;
    margin-top: 16px !important;
}

.metrics div {
    padding: 13px !important;
    background: #fcf9ff !important;
    border: 1px solid #eadcff !important;
    border-radius: 14px !important;
}

.metrics small {
    display: block !important;
    color: #684b78 !important;
}

.metrics b {
    color: #291039 !important;
}


/* INPUTS */

.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    background: #ffffff !important;
    color: #24132f !important;
    border: 1px solid #d6b8ee !important;
    border-radius: 13px !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: #80648d !important;
}

.gradio-container label {
    color: #4b2863 !important;
    font-weight: 700 !important;
}


/* BUTTONS */

.gradio-container button.primary {
    background:
        linear-gradient(
            135deg,
            #7e22ce,
            #a21caf,
            #db2777
        ) !important;

    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;

    box-shadow:
        0 8px 20px rgba(162,28,175,.20) !important;
}


/* TABS */

.gradio-container .tab-nav {
    background: #ffffff !important;
    border-bottom: 1px solid #dfc9f4 !important;

    display: flex !important;
    overflow-x: auto !important;
    white-space: nowrap !important;
}

.gradio-container .tab-nav button {
    color: #5b3b6d !important;
    background: transparent !important;
    font-weight: 700 !important;
    flex: 0 0 auto !important;
}

.gradio-container .tab-nav button:hover {
    color: #7e22ce !important;
    background: #faf5ff !important;
}

.gradio-container .tab-nav button.selected {
    color: #7e22ce !important;
    border-bottom: 3px solid #c026d3 !important;
}


/* MARKDOWN */

.gradio-container .markdown,
.gradio-container .prose {
    color: #24132f !important;
    background: #ffffff !important;
}

.gradio-container .markdown p,
.gradio-container .markdown li,
.gradio-container .prose p,
.gradio-container .prose li {
    color: #24132f !important;
    line-height: 1.7 !important;
}


/* TABLE */

.gradio-container table {
    background: #ffffff !important;
}

.gradio-container th {
    background: #f4eafe !important;
    color: #4b2863 !important;
}

.gradio-container td {
    background: #ffffff !important;
    color: #24132f !important;
}


/* STATUS */

.error {
    background: #fff1f7 !important;
    color: #9f1239 !important;
    border: 1px solid #f9c8df !important;
    border-radius: 16px !important;
    padding: 16px !important;
}

.success {
    background: #f7efff !important;
    color: #6b21a8 !important;
    border: 1px solid #dfc4fb !important;
    border-radius: 16px !important;
    padding: 16px !important;
}


@media (max-width: 700px) {

    .kpis {
        grid-template-columns: repeat(2,1fr) !important;
    }

    .metrics {
        grid-template-columns: repeat(2,1fr) !important;
    }

    .hero {
        padding: 26px 22px !important;
    }

    .hero h1 {
        font-size: 30px !important;
    }
}


footer {
    display: none !important;
}

"""


# ============================================================
# BUILD APP
# ============================================================

with gr.Blocks(
    title="TravelOps Client Intelligence Console",
    css=CSS
) as demo:

    # ========================================================
    # HERO
    # ========================================================

    gr.HTML(
        """
        <div class="hero">

            <span class="badge">
                TRAVELOPS AI
            </span>

            <h1>
                Travel Agency Operations Center
            </h1>

            <p>
                AI-powered employee workspace for
                flights, hotels, bookings, refunds,
                customer support and travel planning.
            </p>

            <div class="chips">

                <span>✈ Flights</span>
                <span>🏨 Hotels</span>
                <span>🎫 Bookings</span>
                <span>💳 Refunds</span>
                <span>🤖 AI Support</span>
                <span>🗺 Trip Planner</span>
                <span>🧭 Travel Advisor</span>

            </div>

        </div>
        """
    )


    # ========================================================
    # DASHBOARD
    # ========================================================

    dashboard = gr.HTML(
        value=dashboard_html()
    )


    # ========================================================
    # TABS
    # ========================================================

    with gr.Tabs():

        # ====================================================
        # CLIENT SETUP
        # ====================================================

        with gr.Tab("Client Setup"):

            gr.Markdown(
                """
                ## 📂 Client Workspace Setup

                Upload the client's operational Excel file
                and company policy PDF.
                """
            )

            with gr.Row():

                client_excel = gr.File(
                    label="Travel Data Excel",
                    file_types=[".xlsx", ".xls"],
                    type="filepath"
                )

                client_policy = gr.File(
                    label="Company Policy PDF",
                    file_types=[".pdf"],
                    type="filepath"
                )

            load_client_btn = gr.Button(
                "Load Client Workspace",
                variant="primary"
            )

            client_status = gr.Markdown(
                "No client data loaded yet."
            )





        # ====================================================
        # FLIGHT SEARCH
        # ====================================================

        with gr.Tab("Flight Search"):

            gr.Markdown(
                """
                ## ✈ Flight Search

                Search verified flights from the client's
                uploaded travel inventory.
                """
            )

            with gr.Row():

                origin = gr.Dropdown(
                    choices=[],
                    label="Origin",
                    allow_custom_value=True
                )

                destination = gr.Dropdown(
                    choices=[],
                    label="Destination",
                    allow_custom_value=True
                )

            flight_btn = gr.Button(
                "🔎 Search Flights",
                variant="primary"
            )

            flight_msg = gr.Markdown()

            flight_df = gr.Dataframe(
                interactive=False,
                wrap=True
            )


        # ====================================================
        # BOOKING TRACKING
        # ====================================================

        with gr.Tab("Booking Tracking"):

            gr.Markdown(
                """
                ## 🎫 Booking Tracking

                Verify a customer's booking.
                """
            )

            booking_id = gr.Dropdown(
                choices=[],
                label="Booking ID",
                allow_custom_value=True
            )

            booking_btn = gr.Button(
                "Check Booking",
                variant="primary"
            )

            booking_card = gr.HTML(
                "<div class='detail'>"
                "Enter a Booking ID."
                "</div>"
            )

            booking_raw = gr.Dataframe(
                interactive=False,
                label="Verified Booking Data"
            )


        # ====================================================
        # HOTEL SEARCH
        # ====================================================

        with gr.Tab("Hotel Search"):

            gr.Markdown(
                """
                ## 🏨 Hotel Search

                Search the client's verified hotel inventory.
                """
            )

            hotel_city = gr.Dropdown(
                choices=[],
                label="City",
                allow_custom_value=True
            )

            hotel_btn = gr.Button(
                "🔎 Search Hotels",
                variant="primary"
            )

            hotel_msg = gr.Markdown()

            hotel_df = gr.Dataframe(
                interactive=False,
                wrap=True
            )


        # ====================================================
        # REFUND CONTROL
        # ====================================================

        with gr.Tab("Refund Control"):

            gr.Markdown(
                """
                ## 💳 Refund Control

                Refund requests remain **Pending**
                until human approval.
                """
            )

            refund_booking = gr.Dropdown(
                choices=[],
                label="Booking ID",
                allow_custom_value=True
            )

            refund_reason = gr.Textbox(
                label="Reason",
                value="Customer cancellation",
                lines=3
            )

            refund_btn = gr.Button(
                "Create Refund Request",
                variant="primary"
            )

            refund_status = gr.HTML(
                "<div class='detail'>"
                "No refund request created."
                "</div>"
            )

            refund_df = gr.Dataframe(
                value=refund_table(),
                label="Refund Register",
                interactive=False
            )


        # ====================================================
        # SUPPORT ASSISTANT
        # ====================================================

        with gr.Tab("Support Assistant"):

            gr.Markdown(
                """
                ## 🤖 AI Customer Support Assistant

                Verify booking + company policy +
                Groq AI response.
                """
            )

            support_booking = gr.Dropdown(
                choices=[],
                label="Booking ID",
                allow_custom_value=True
            )

            issue = gr.Textbox(
                label="Customer Question",
                value=(
                    "Can I cancel my booking "
                    "and get a refund?"
                ),
                lines=5
            )

            support_btn = gr.Button(
                "Generate Verified Response",
                variant="primary"
            )

            support_answer = gr.Markdown(
                "Response will appear here."
            )

            with gr.Accordion(
                "Show MCP Evidence",
                open=False
            ):

                support_evidence = gr.Markdown()


        # ====================================================
        # TRIP PLANNER
        # ====================================================

        with gr.Tab("Trip Planner"):

            gr.Markdown(
                """
                ## 🗺️ AI Trip Planner

                Groq AI creates the itinerary using
                verified client travel data.
                """
            )

            trip_destination = gr.Dropdown(
                choices=[],
                label="Destination",
                allow_custom_value=True
            )

            trip_dates = gr.Dropdown(
                choices=[],
                label="Travel Dates",
                allow_custom_value=True
            )

            trip_budget = gr.Textbox(
                label="Budget",
                placeholder="$1000"
            )

            trip_btn = gr.Button(
                "✨ Plan Trip",
                variant="primary"
            )

            trip_result = gr.Markdown(
                "Your travel plan will appear here."
            )

            trip_hotels = gr.Dataframe(
                interactive=False,
                wrap=True
            )


        # ====================================================
        # TRAVEL ADVISOR
        # ====================================================

        with gr.Tab("Travel Advisor"):

            gr.Markdown(
                """
                ## 🧭 AI Travel Advisor

                Provide recommendations based on
                destination, budget and preference.
                """
            )

            advisor_destination = gr.Dropdown(
                choices=[],
                label="Destination",
                allow_custom_value=True
            )

            advisor_budget = gr.Textbox(
                label="Budget",
                placeholder="$1500"
            )

            advisor_preference = gr.Dropdown(
                choices=[
                    "Luxury",
                    "Budget",
                    "Family",
                    "Business",
                    "Beach",
                    "Convenient location"
                ],
                label="Preference",
                allow_custom_value=True
            )

            advisor_btn = gr.Button(
                "✨ Get Travel Advice",
                variant="primary"
            )

            advisor_result = gr.Markdown(
                "Travel advice will appear here."
            )

            advisor_hotels = gr.Dataframe(
                interactive=False,
                wrap=True
            )


        # ====================================================
        # MCP EXPLORER
        # ====================================================

        with gr.Tab("MCP Explorer"):

            gr.Markdown(
                """
                ## 🔧 MCP Capability Explorer

                Discover the tools, resources and
                prompts exposed by TravelOps.
                """
            )

            explorer_btn = gr.Button(
                "Discover MCP Capabilities",
                variant="primary"
            )

            explorer_df = gr.Dataframe(
                interactive=False,
                wrap=True
            )


    # ========================================================
    # EVENT HANDLERS
    # IMPORTANT: THESE ARE INSIDE with gr.Blocks
    # ========================================================

    # --------------------------------------------------------
    # LOAD CLIENT
    # --------------------------------------------------------

    load_client_btn.click(
        fn=load_client_workspace,
        inputs=[
            client_excel,
            client_policy
        ],
        outputs=[
            client_status,
            dashboard
        ]
    ).then(
        fn=get_dropdown_updates,
        inputs=None,
        outputs=[
            origin,
            destination,
            booking_id,
            hotel_city,
            trip_destination,
            trip_dates,
            advisor_destination,
            advisor_preference,
            refund_booking,
            support_booking
        ]
    )


    # --------------------------------------------------------
    # REFRESH DASHBOARD
    # --------------------------------------------------------

    refresh.click(
        fn=dashboard_html,
        inputs=None,
        outputs=dashboard
    )


    # --------------------------------------------------------
    # FLIGHT SEARCH
    # --------------------------------------------------------

    flight_btn.click(
        fn=ui_search_flights,
        inputs=[
            origin,
            destination
        ],
        outputs=[
            flight_df,
            flight_msg
        ]
    )


    # --------------------------------------------------------
    # BOOKING
    # --------------------------------------------------------

    booking_btn.click(
        fn=ui_booking,
        inputs=booking_id,
        outputs=[
            booking_card,
            booking_raw
        ]
    )


    # --------------------------------------------------------
    # HOTEL SEARCH
    # --------------------------------------------------------

    hotel_btn.click(
        fn=ui_hotels,
        inputs=hotel_city,
        outputs=[
            hotel_df,
            hotel_msg
        ]
    )


    # --------------------------------------------------------
    # REFUND
    # --------------------------------------------------------

    refund_btn.click(
        fn=ui_refund,
        inputs=[
            refund_booking,
            refund_reason
        ],
        outputs=[
            refund_status,
            refund_df
        ]
    ).then(
        fn=dashboard_html,
        inputs=None,
        outputs=dashboard
    )


    # --------------------------------------------------------
    # SUPPORT
    # --------------------------------------------------------

    support_btn.click(
        fn=ui_support,
        inputs=[
            support_booking,
            issue
        ],
        outputs=[
            support_answer,
            support_evidence
        ]
    )


    # --------------------------------------------------------
    # TRIP PLANNER
    # --------------------------------------------------------

    trip_btn.click(
        fn=ui_trip_planner,
        inputs=[
            trip_destination,
            trip_dates,
            trip_budget
        ],
        outputs=[
            trip_result,
            trip_hotels
        ]
    )


    # --------------------------------------------------------
    # TRAVEL ADVISOR
    # --------------------------------------------------------

    advisor_btn.click(
        fn=ui_travel_advisor,
        inputs=[
            advisor_destination,
            advisor_budget,
            advisor_preference
        ],
        outputs=[
            advisor_result,
            advisor_hotels
        ]
    )


    # --------------------------------------------------------
    # MCP EXPLORER
    # --------------------------------------------------------

    explorer_btn.click(
        fn=ui_explorer,
        inputs=None,
        outputs=explorer_df
    )


print("✅ TravelOps UI and all event handlers created.")

# ===== CELL 80 =====
# ============================================================
# LAUNCH
# ============================================================

if __name__ == "__main__":
    demo.queue().launch()
