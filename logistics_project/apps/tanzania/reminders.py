from django.core.mail import mail_admins


def test_email_admins():
    """
    Just a proof of concept to test the scheduler. 
    """
    mail_admins("Scheduler test", "This is your reminder that all is well")
    