from djoser import email
from django.conf import settings
import boto3

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
        
        # Now verify the user in Cognito
        self.verify_in_cognito(to[0])  # to is a list of emails
        
        return result
    
    def verify_in_cognito(self, email):
        try:
            # Initialize Cognito client
            client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION)
            
            # Find the user by email in Cognito
            response = client.list_users(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Filter=f'email = "{email}"',
                Limit=1
            )
            
            if response['Users']:
                cognito_username = response['Users'][0]['Username']
                
                # Verify the user's email in Cognito
                client.admin_update_user_attributes(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=cognito_username,
                    UserAttributes=[
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        }
                    ]
                )
                
            else:
                print(f"User with email {email} not found in Cognito")
                
        except Exception as e:
            print(f"Error verifying user in Cognito: {str(e)}")

class PasswordResetEmail(email.PasswordResetEmail):
    template_name = 'auth/password_reset.html'