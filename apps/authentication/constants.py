from djoser.constants import Messages as DefaultMessages


class Messages(DefaultMessages):
    ACTIVATION_SUCCESSFUL = "Your account has been activated successfully!"
    PASSWORD_RESET_CONFIRM_INVALID_TOKEN = "Invalid password reset token."
    SET_PASSWORD_RETYPE_PASSWORD_ERROR = "The two password fields didn't match."
    PASSWORD_CHANGED_CONFIRMATION = "Password changed successfully."
