from django.contrib.sites.models import Site
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound
import logging

from ..utils import require_active_plugin, get_supported_currencies
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from .yookassa_api import create_payment
from ...interface import (
    CustomerSource,
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
    StorePaymentMethodEnum,
)

logger = logging.getLogger(__name__)

GATEWAY_NAME = "Yookassa"
WEBHOOK_PATH = "/webhooks"
ADDITIONAL_ACTION_PATH = "/additional-actions"


class YookassaGatewayPlugin(BasePlugin):
    PLUGIN_NAME = 'Yookassa'
    PLUGIN_ID = "mirumee.payments.yookassa_payment"
    DEFAULT_CONFIGURATION = [
        {"name": "public_api_key", "value": None},
        {"name": "secret_api_key", "value": None},
        {"name": "automatic_payment_capture", "value": True},
        {"name": "return_url", "value": ""},
        {"name": "webhook_endpoint_id", "value": None},
        {"name": "webhook_secret_key", "value": None},
    ]
    CONFIG_STRUCTURE = {
        "public_api_key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide Yookassa public API key.",
            "label": "Public API key",
        },
        "secret_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Yookassa secret API key.",
            "label": "Secret API key",
        },
        "automatic_payment_capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automatically capture payments.",
            "label": "Automatic payment capture",
        },
        "return_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Website return address",
            "label": "Supported currencies",
        },
        "webhook_endpoint_id": {
            "type": ConfigurationTypeField.OUTPUT,
            "help_text": "Unique identifier for the webhook endpoint object.",
            "label": "Webhook endpoint",
        },
    }

    def __init__(self, *args, **kwargs):
        # Webhook details are not listed in CONFIG_STRUCTURE as user input is not
        # required here
        plugin_configuration = kwargs.get("configuration")
        raw_configuration = {
            item["name"]: item["value"] for item in plugin_configuration
        }
        webhook_secret = raw_configuration.get("webhook_secret_key")

        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=self.PLUGIN_NAME,
            auto_capture=configuration["automatic_payment_capture"],
            supported_currencies=configuration["supported_currencies"],
            connection_params={
                "public_api_key": configuration["public_api_key"],
                "secret_api_key": configuration["secret_api_key"],
                "webhook_id": configuration["webhook_endpoint_id"],
                "webhook_secret": webhook_secret,
            },
            store_customer=True,
        )

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        config = self.config
        if path.startswith(WEBHOOK_PATH, 1):  # 1 as we don't check the '/'
            return handle_webhook(request, config, self.channel.slug)  # type: ignore
        logger.warning(
            "Received request to incorrect stripe path", extra={"path": path}
        )
        return HttpResponseNotFound()

    @require_active_plugin
    def token_is_required_as_payment_input(self, previous_value):
        return False

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        return get_supported_currencies(self.config, self.PLUGIN_NAME)

    @property
    def order_auto_confirmation(self):
        site_settings = Site.objects.get_current().settings
        return site_settings.automatically_confirm_all_new_orders

    @require_active_plugin
    def process_payment(
            self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        api_key = self.config.connection_params["secret_api_key"]

        data = payment_information.data

        payment_method_id = data.get("payment_method").get('id') if data else None

        payment_method_types = data.get("payment_method_types") if data else None

        customer = None
        # confirm that we creates customer on stripe side only for log-in customers
        # Stripe doesn't allow to search users by email, so each create customer
        # call creates new customer on Stripe side.
        intent, error = create_payment(
            value=payment_information.amount,
            return_url='',
            description=payment_information.payment_metadata,
        )

        client_secret = None
        intent_id = None
        action_required = True
        payment_method_info = None
        if intent:
            kind, action_required = self._get_transaction_details_for_stripe_status(
                intent.status
            )

        return GatewayResponse(
            is_success=True if not error else False,
            action_required=action_required,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=intent.id if intent else "",
            error=error.user_message if error else None,
            action_required_data={"client_secret": client_secret, "id": intent_id},
            customer_id=customer.id if customer else None,
            psp_reference=intent.id if intent else None,
            payment_method_info=payment_method_info,
        )
