"""
from exchangelib import Credentials, Account, Message, DELEGATE, IMPERSONATION, Configuration

def send_outlook_email():
    # Replace these with your Outlook credentials and recipient email address
    outlook_email = "ssirish@dsi.com"
    outlook_password = ""
    recipient_email = "ssirish@dsi.com"
    # ssirish@dsi.com
    # ssirish@daiichisankyo.com
    # sidharth.sirish@daiichisankyo.com

    # Set up credentials
    # credentials = Credentials(outlook_email, outlook_password)
    credentials = Credentials(username="ssirish@dsi.com", password=outlook_password)
    config = Configuration(server="outlook.office365.com", credentials=credentials)

    # Connect to the Outlook account
    # myaccount = Account(outlook_email, credentials=credentials, autodiscover=True, access_type=DELEGATE)
    # myaccount = Account(primary_smtp_address="ssirish@dsi.com", credentials=credentials, autodiscover=True, access_type=DELEGATE)
    # myaccount = Account(primary_smtp_address="ssirish@dsi.com", config=config, autodiscover=False, access_type=DELEGATE)
    myaccount = Account(outlook_email, config=config, autodiscover=False, access_type=DELEGATE)

    myaccount.ad_response

    # Create a simple email message
    email = Message(
        account=myaccount,
        subject='Test Email from Python',
        body='Hello, this is a test email sent from Python.',
        to_recipients=[recipient_email]
    )

    # Send the email
    email.send()

    print("Email sent successfully.")

if __name__ == "__main__":
    send_outlook_email()
"""


from exchangelib import Credentials, Account, Message, DELEGATE, HTMLBody

def send_outlook_email():
    # Replace these with your organizational Outlook credentials and recipient email address
    outlook_email = ""
    app_password = ""  # Use the app password you generated
    recipient_email = ""

    # Set up credentials with the App Password
    credentials = Credentials(outlook_email, app_password)

    # Connect to the Outlook account with Autodiscover
    account = Account(primary_smtp_address=outlook_email, credentials=credentials, autodiscover=True, access_type=DELEGATE)

    # Create a simple email message
    email = Message(
        account=account,
        subject='Test Email from Python',
        body=HTMLBody('<p>Hello, this is a test email sent from Python.</p>'),
        to_recipients=[recipient_email]
    )

    # Send the email
    email.send()

    print("Email sent successfully.")

if __name__ == "__main__":
    send_outlook_email()

