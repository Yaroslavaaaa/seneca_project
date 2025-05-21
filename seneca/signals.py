from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import mail_admins
from .models import Application

@receiver(post_save, sender=Application)
def notify_admin_new_application(sender, instance, created, **kwargs):
    if not created:
        return

    subject = f'Новая заявка от {instance.name}'
    message = (
        f'Поступила новая заявка:\n\n'
        f'ID:    {instance.id}\n'
        f'Имя:   {instance.name}\n'
        f'Телефон: {instance.phone}\n'
        f'Дата:  {instance.created_at.strftime("%Y-%m-%d %H:%M")}\n'
    )
    mail_admins(subject, message)
