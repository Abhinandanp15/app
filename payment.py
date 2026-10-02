import razorpay

client = razorpay.Client(auth=("rzp_test_SVlRvoWboMqsNI", "ChiyhfXMyFISKc0GdmOUTA3G"))

def create_order(amount):
    order = client.order.create({
        "amount": int(amount * 100),  # paise
        "currency": "INR",
        "payment_capture": 1
    })
    return order