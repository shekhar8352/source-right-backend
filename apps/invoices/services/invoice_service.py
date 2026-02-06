from shared.logging import get_logger

logger = get_logger(__name__)


def create_invoice(invoice_id: str, amount: int) -> None:
    logger.info(
        "Invoice created",
        extra={
            "invoice_id": invoice_id,
            "amount": amount,
        },
    )
