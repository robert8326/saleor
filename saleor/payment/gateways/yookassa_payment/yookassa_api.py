from yookassa import Configuration, Payment
import uuid

Configuration.account_id = ''
Configuration.secret_key = ''


def create_payment(value, return_url, description=None):
    payment = Payment.create({
        "amount": {
            "value": f"{value}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{return_url}"
        },
        "description": f"Заказ №{description or '-1'}"
    }, uuid.uuid4())
    return payment, None
