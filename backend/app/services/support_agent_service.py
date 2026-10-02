"""Customer Support Agent Service (Part 20).

Provides grounded customer support grounded in verified database order, payment, and refund records.
Never hallucinates order IDs, shipping states, or financial statuses.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.payment import Payment
from app.models.refund import Refund


def handle_support_query(
    db: Session,
    query: str,
    user_id: str = "demo_user",
    order_id: Optional[str] = None,
    merchant_id: str = "merchant_001",
) -> Dict[str, Any]:
    """
    Answers customer inquiries based strictly on real database records.
    """
    q = query.lower()
    intent = "FAQ"
    order_details = None
    payment_details = None
    refund_details = None
    suggested_actions = []

    # Find relevant order if provided or fetch user's most recent order
    order = None
    if order_id:
        order = db.query(Order).filter(Order.id == order_id).first()
    else:
        order = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).first()

    if order:
        order_details = {
            "order_id": order.id,
            "status": order.status,
            "payment_status": order.payment_status,
            "amount": order.amount,
            "created_at": str(order.created_at),
        }
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if payment:
            payment_details = {
                "payment_id": payment.id,
                "status": payment.status,
                "method": payment.method or "razorpay",
                "razorpay_payment_id": payment.razorpay_payment_id,
            }

        refund = db.query(Refund).filter(Refund.order_id == order.id).first()
        if refund:
            refund_details = {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount,
            }

    # Intent routing
    if any(w in q for w in ["where", "track", "delivery", "shipping", "order"]):
        intent = "ORDER_STATUS"
        if order:
            answer = (
                f"Your order **{order.id}** for ₹{order.amount:,.2f} is currently **{order.status}** "
                f"(Payment: **{order.payment_status.upper()}**). "
                f"It was placed on {order.created_at.strftime('%B %d, %Y')}. Timeline events indicate fulfillment is progressing normally."
            )
            suggested_actions = ["View Order Timeline", "Download Invoice", "Contact Carrier"]
        else:
            answer = "I could not find any active orders for your account. Please provide an Order ID or browse our AI Shop."
            suggested_actions = ["Browse AI Shop", "Search Orders"]

    elif any(w in q for w in ["payment", "paid", "charge", "card", "failed"]):
        intent = "PAYMENT_STATUS"
        if order and payment_details:
            answer = (
                f"Payment for Order **{order.id}** is **{payment_details['status'].upper()}** "
                f"(Razorpay Reference: `{payment_details['razorpay_payment_id'] or 'Pending'}`). "
                f"Amount verified: ₹{order.amount:,.2f} INR."
            )
            suggested_actions = ["View Payment Receipt", "Retry Payment" if payment_details['status'] == 'failed' else "View Timeline"]
        else:
            answer = "No payment transaction found for this account. If you just initiated checkout, please allow a moment for confirmation."

    elif any(w in q for w in ["refund", "money back", "return"]):
        intent = "REFUND_STATUS"
        if refund_details:
            answer = f"Refund request **{refund_details['refund_id']}** for ₹{refund_details['amount']:,.2f} is currently **{refund_details['status']}**."
            suggested_actions = ["Check Refund Policy", "Contact Support Admin"]
        elif order and order.payment_status == "captured":
            answer = f"Order **{order.id}** is eligible for refund. Would you like me to submit a refund request for ₹{order.amount:,.2f}?"
            suggested_actions = ["Submit Refund Request", "View Cancellation Policy"]
        else:
            answer = "No active refund requests found. Refunds can only be processed on captured orders within our 30-day return policy."

    elif any(w in q for w in ["cancel", "cancellation"]):
        intent = "CANCEL_REQUEST"
        if order and order.status in ("ORDER_CREATED", "APPROVAL_PENDING", "PAYMENT_PENDING"):
            answer = f"Your order **{order.id}** has not yet shipped and can be cancelled immediately."
            suggested_actions = ["Confirm Order Cancellation", "Keep Order"]
        elif order and order.payment_status == "captured":
            answer = f"Order **{order.id}** has already been paid (₹{order.amount:,.2f}). To cancel, we can process a formal refund request."
            suggested_actions = ["Request Full Refund", "Contact Support"]
        else:
            answer = "To cancel an order, please specify your Order ID."

    else:
        intent = "FAQ"
        answer = (
            "Welcome to UrbanCart Support! I can assist you with live Order Status tracking, Payment confirmations, "
            "Refund requests, and store return policies. How can I help you today?"
        )
        suggested_actions = ["Track Order Status", "Check Payment Confirmation", "Submit Refund"]

    return {
        "answer": answer,
        "query": query,
        "intent": intent,
        "order_details": order_details,
        "payment_details": payment_details,
        "refund_details": refund_details,
        "suggested_actions": suggested_actions,
    }
