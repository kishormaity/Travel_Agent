from loguru import logger
from langchain_core.tools import tool
from app.services.currency_service import CurrencyService
from app.schemas.tool_result import ToolResult

_currency_service = CurrencyService()


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> ToolResult:
    """Convert money from one currency into another (e.g. 30000 INR to USD)."""
    logger.info(f"Currency Tool invoked: {amount} {from_currency} -> {to_currency}")
    try:
        data = _currency_service.convert_currency(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
        )
        return ToolResult(success=True, data=data)
    except Exception as e:
        logger.warning(f"Currency Tool failed: {e}")
        return ToolResult(success=False, error=str(e), data={})


class CurrencyTool:
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> ToolResult:
        return convert_currency.invoke({
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
        })