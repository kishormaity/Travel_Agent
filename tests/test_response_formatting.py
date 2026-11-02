import re
import pytest
from app.agents.response_agent import clean_travel_report_formatting, EMOJI_PATTERN


def test_clean_travel_report_formatting_removes_hashes():
    """Verify markdown heading hashes like ## and ### are stripped from line starts."""
    raw = "## Trip Overview\nThis is a trip.\n### Flight Details\nFlight info here."
    cleaned = clean_travel_report_formatting(raw)
    assert "##" not in cleaned
    assert "###" not in cleaned
    assert "Trip Overview" in cleaned
    assert "Flight Details" in cleaned


def test_clean_travel_report_formatting_removes_bold_and_italics():
    """Verify bold markers **word** and __word__ are removed while text is preserved."""
    raw = "The total price is **₹70,601** with **IndiGo** airline on __10 January__."
    cleaned = clean_travel_report_formatting(raw)
    assert "**" not in cleaned
    assert "__" not in cleaned
    assert "The total price is ₹70,601 with IndiGo airline on 10 January." in cleaned


def test_clean_travel_report_formatting_removes_emojis():
    """Verify decorative emojis and circled number symbols are stripped."""
    raw = "1️⃣ Flight Summary ✈️\n2️⃣ Accommodation 🏨\nDay 1 🚗 Arrive in Kochi 🌴"
    cleaned = clean_travel_report_formatting(raw)
    assert not EMOJI_PATTERN.search(cleaned)
    assert "✈️" not in cleaned
    assert "🏨" not in cleaned
    assert "🚗" not in cleaned
    assert "🌴" not in cleaned
    assert "Flight Summary" in cleaned
    assert "Accommodation" in cleaned
    assert "Arrive in Kochi" in cleaned


def test_clean_travel_report_formatting_preserves_tables():
    """Verify markdown table pipes and structure are preserved without bold text in cells."""
    raw = """| **Leg** | **Airline / Flight** | **Price** |
|---|---|---|
| **Outbound** | **IndiGo (6E6262)** | **₹33,606** |
| **Return** | **IndiGo (6E5046)** | **₹34,865** |"""
    cleaned = clean_travel_report_formatting(raw)
    assert "**" not in cleaned
    assert "| Leg | Airline / Flight | Price |" in cleaned
    assert "| Outbound | IndiGo (6E6262) | ₹33,606 |" in cleaned
    assert "| Return | IndiGo (6E5046) | ₹34,865 |" in cleaned


def test_clean_travel_report_formatting_removes_blockquotes_and_excessive_colons():
    """Verify blockquote markers and multiple consecutive colons are cleaned."""
    raw = "> Important Note:: The budget is insufficient."
    cleaned = clean_travel_report_formatting(raw)
    assert ">" not in cleaned
    assert "::" not in cleaned
    assert "Important Note: The budget is insufficient." in cleaned


def test_clean_travel_report_comprehensive_validation():
    """Comprehensive test validating all formatting requirements on a full mock travel report."""
    raw_mock = """## 1️⃣ Trip Overview 🌍
> **Note:** Confirmed bookings require immediate payment.

### 2️⃣ Flight Details ✈️
| **Leg** | **Airline** | **Price** |
|---|---|---|
| **Outbound** | **IndiGo** | **₹33,606** |

### 3️⃣ Accommodation Options 🏨
* **Grand Hyatt Kochi**: 5-star hotel with 4.7★ rating.
* **Tea County Munnar**: 4-star resort.

### 4️⃣ Estimated Budget 💰
Total confirmed spend:: **₹70,601**.
Remaining balance:: **₹19,399**.
"""

    cleaned = clean_travel_report_formatting(raw_mock)

    # 1. No ## or ###
    assert not re.search(r"^#{1,6}\s", cleaned, flags=re.MULTILINE)
    # 2. No ** or __
    assert "**" not in cleaned
    assert "__" not in cleaned
    # 3. No emojis
    assert not EMOJI_PATTERN.search(cleaned)
    # 4. No excessive colons
    assert "::" not in cleaned
    # 5. Tables preserved
    assert "| Leg | Airline | Price |" in cleaned
    # 6. Section text preserved
    assert "Trip Overview" in cleaned
    assert "Flight Details" in cleaned
    assert "Accommodation Options" in cleaned
    assert "Estimated Budget" in cleaned
