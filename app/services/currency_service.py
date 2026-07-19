import httpx
from loguru import logger
from app.config import CURRENCY_API_BASE_URL


class CurrencyService:
    """
    Handles communication with the Frankfurter Currency API.
    """

    def __init__(self):
        self.base_url = CURRENCY_API_BASE_URL

    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> dict:
        """
        Convert an amount from one currency to another.

        Args:
            amount: Amount to convert.
            from_currency: Source currency code (e.g. USD).
            to_currency: Target currency code (e.g. INR).

        Returns:
            Dictionary containing conversion result.
        """

        if not from_currency.strip() or not to_currency.strip():
            raise ValueError(
                "Source and target currencies cannot be empty."
            )

        if amount <= 0:
            raise ValueError(
                "Amount must be greater than zero."
            )

        endpoint = f"{self.base_url}/latest"

        params = {
            "amount": amount,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
        }

        try:

            with httpx.Client(
                timeout=10.0,
                follow_redirects=True,
            ) as client:

                response = client.get(
                    endpoint,
                    params=params,
                )

                if response.status_code != 200:
                    try:
                        err_body = response.json()
                        err_msg = err_body.get("message")
                        if err_msg:
                            raise Exception(f"Currency API error message: {err_msg}")
                    except Exception as e:
                        if "Currency API error message" in str(e):
                            raise e

                response.raise_for_status()

                data = response.json()

                from app.schemas.api.response_models import CurrencyResponseModel
                validated = CurrencyResponseModel.model_validate(data)

                if validated.rates is None or to_currency.upper() not in validated.rates:
                    raise ValueError(
                        f"Invalid currency code: {to_currency.upper()}"
                    )

                converted_amount = validated.rates[to_currency.upper()]

                logger.info(
                    f"Currency converted successfully: "
                    f"{amount} {from_currency.upper()} -> "
                    f"{converted_amount} {to_currency.upper()}"
                )

                return {
                    "amount": validated.amount,
                    "from_currency": validated.base,
                    "to_currency": to_currency.upper(),
                    "converted_amount": converted_amount,
                    "exchange_rate": converted_amount / amount,
                    "date": validated.date,
                }

        except httpx.HTTPStatusError as error:

            logger.error(
                f"Currency API Error: {error.response.text}"
            )

            raise Exception(
                f"Failed to convert {amount} {from_currency.upper()} to "
                f"{to_currency.upper()}."
            ) from error

        except httpx.RequestError as error:

            logger.error(
                f"Unable to connect to Frankfurter API: {error}"
            )

            raise Exception(
                "Unable to connect to Currency API."
            ) from error

        except Exception as error:

            logger.exception(
                f"Unexpected error while converting currency: {error}"
            )

            raise