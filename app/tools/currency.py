from loguru import logger

from app.services.currency_service import CurrencyService


class CurrencyTool:
    """
    Tool responsible for currency conversion.
    """

    def __init__(self):
        self.currency_service = CurrencyService()

    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> dict:
        """
        Convert one currency into another.
        """

        logger.info(
            f"Currency Tool invoked: "
            f"{amount} {from_currency} -> {to_currency}"
        )

        return self.currency_service.convert_currency(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
        )