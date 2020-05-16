from django.contrib.auth import forms
from django.core.mail import send_mail as sm
from django.template import loader


class PasswordResetForm(forms.PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        sm(subject, body, from_email, [to_email], fail_silently=False)
