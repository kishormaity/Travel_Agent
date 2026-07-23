from loguru import logger
from langchain_core.tools import tool
from app.services.currency_service import CurrencyService

_currency_service = CurrencyService()


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert money from one currency into another (e.g. 30000 INR to USD)."""
    logger.info(f"Currency Tool invoked: {amount} {from_currency} -> {to_currency}")
    return _currency_service.convert_currency(
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
    )


class CurrencyTool:
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> dict:
        return convert_currency.invoke({
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
        })