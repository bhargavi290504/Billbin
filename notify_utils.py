# import smtplib
# from email.message import EmailMessage

# def send_notification(email, balance):
#     msg = EmailMessage()
#     msg.set_content(f"Alert! Your remaining balance is ₹{balance}.")
#     msg['Subject'] = 'Billbin Low Balance Alert'
#     msg['From'] = 'your-email@gmail.com'
#     msg['To'] = email

#     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
#         smtp.login('bhargavi2026@gmail.com', 'btpbiffynwevjjf')
#         smtp.send_message(msg)
import smtplib

def send_notification(to_email, remaining_balance):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender_email = 'bhargavi2026@gmail.com'
    sender_password = 'aeophpltfknkomao'  
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = 'Low Balance Notification'

    body = f"Your remaining balance is {remaining_balance}. Please check your spending."
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            text = message.as_string()
            server.sendmail(sender_email, to_email, text)
            print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
