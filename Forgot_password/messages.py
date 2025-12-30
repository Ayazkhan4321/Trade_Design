"""User-visible messages for the Forgot Password feature.

Keeping messages in a separate module makes them easy to test and localize later.
"""

MSG_SENT = "Password reset link has been sent to your email address. Please check your email and follow the instructions."
MSG_EXPLICIT_SENT_TEMPLATE = "Password reset link has been sent to {email}."
MSG_NOT_REGISTERED = "The email address is not registered."