from djoser import email

class ActivationEmail(email.ActivationEmail):
    template_name = 'auth/activation.html'
    
    def send(self, to, *args, **kwargs):
        # Send the regular activation email
        super().send(to, *args, **kwargs)

class ConfirmationEmail(email.ConfirmationEmail):
    template_name = 'auth/confirmation.html'
    
    def send(self, to, *args, **kwargs):
        # Send the regular confirmation email
        result = super().send(to, *args, **kwargs)
        
        return result


class PasswordResetEmail(email.PasswordResetEmail):
    template_name = 'auth/password_reset.html'

    def send(self, to, *args, **kwargs):
        # Send the regular confirmation email
        result = super().send(to, *args, **kwargs)
        
        return result
    

class PasswordChangedConfirmationEmail(email.PasswordResetEmail):
    template_name = 'auth/password_changed_confirmation.html'

    def send(self, to, *args, **kwargs):
        # Send the regular confirmation email
        result = super().send(to, *args, **kwargs)
        
        return result
