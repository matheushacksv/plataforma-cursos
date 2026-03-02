from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_password_reset_email(user_email, senha_aleatoria):
    subject = 'Recuperação de Senha'
    message = f'''
    Olá,

    Você solicitou a recuperação de senha. Aqui está sua nova senha

    {senha_aleatoria}

    Utilize para fazer login e troque sua senha no perfil.

    Atenciosamente,
    Equipe de Suporte
    '''
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list)

    return 'Email enviado com sucesso!'