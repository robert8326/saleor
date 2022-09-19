WEBHOOK_PATH = "webhooks/"

WEBHOOK_SUCCESS_EVENT = "payment.succeeded"
WEBHOOK_CANCELED_EVENT = "payment.canceled"

WEBHOOK_REFUND_EVENT = "charge.refunded"

WEBHOOK_EVENTS = [
    WEBHOOK_SUCCESS_EVENT,
    WEBHOOK_CANCELED_EVENT,
    WEBHOOK_REFUND_EVENT,
]
METADATA_IDENTIFIER = "saleor-domain"

ACTION_REQUIRED_STATUSES = [
    "requires_payment_method",
    "requires_confirmation",
    "requires_action",
]

FAILED_STATUSES = ["requires_payment_method", "canceled"]

SUCCESS_STATUS = "succeeded"

PROCESSING_STATUS = "processing"

AUTOMATIC_CAPTURE_METHOD = "automatic"
MANUAL_CAPTURE_METHOD = "manual"

