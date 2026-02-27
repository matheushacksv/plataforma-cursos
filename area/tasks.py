from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def enviar_email_1_acesso(email_aluno, senha_provisoria):
    assunto = f'Seu acesso a plataforma OHenriquecedor foi liberado!'

    mensagem = f'''Olá!

    Seu acesso a plataforma OHenriquecedor chegou!

    Seus dados de acesso:
    Login: {email_aluno}
    Senha temporária: {senha_provisoria}

    **Recomendamos que você troque essa senha logo no seu primeiro acesso**

    Um abraço!
    '''

    remetente = settings.EMAIL_HOST_USER

    send_mail(
        assunto,
        mensagem,
        remetente,
        [email_aluno],
        fail_silently=False
    )

    return f'E-mail enviado para {email_aluno} com sucesso!'

@shared_task
def reenviar_email_acesso(email_aluno, senha_provisioria):
    assunto = 'Seu novo acesso na plataforma OHenriquecedor'

    mensagem = f'''Olá!

    Aqui está seu novo acesso

    Seus dados de acesso:
    Login: {email_aluno}
    Senha: {senha_provisioria}

    **Recomendamos que você troque essa senha logo no seu primeiro acesso**

    Um abraço!
    '''

    remetente = settings.EMAIL_HOST_USER

    send_mail(
        assunto,
        mensagem,
        remetente,
        [email_aluno],
        fail_silently=False
    )

    return f'E-mail enviado para {email_aluno} com sucesso!'
