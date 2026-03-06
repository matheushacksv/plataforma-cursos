from user.models import CustomUser
from django.db import models
from django.conf import settings
from datetime import date
import re
from django.utils import timezone

class Course(models.Model):

    class Category(models.TextChoices):
        DEV = 'DEV', 'Desenvolvimento'
        SALES = 'SAL', 'Vendas e Negociação'
        LEADERSHIP = 'LDR', 'Liderança e Gestão'
        CUSTOMER_SUCESS = 'CUS', 'Sucesso do Cliente'
        DESIGN = 'DES', 'Design'
        BUSINESS = 'BUS', 'Negócios'
        MARKETING = 'MKT', 'Marketing'
        FINANCE = 'FIN', 'Finanças'
        HEALTH = 'HEA', 'Saúde e Fitness'
        LIFESTYLE = 'LIF', 'Estilo de vida'
        PHOTOGRAPHY = 'PHO', 'Fotografia'
        MUSIC = 'MUS', 'Música'
        ACADEMIC = 'ACA', 'Acadêmico'
        OTHER = 'OTH', 'Outros'

    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='course_img/', blank=True, null=True)
    description = models.TextField(help_text='Descrição do curso..', null=True, blank=True)
    categories = models.JSONField(default=list)
    checkout_url = models.URLField(blank=True, null=True)
    page_url = models.URLField(blank=True, null=True)

    kiwify_product_id = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text='Cole aqui o ID do produto da Kiwify')

    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Enrollment',
        related_name='courses_joined',
        blank=True
    )

    active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'course')

    @property
    def has_expired(self):
        '''Verifica se a data de hoje passou a data de fim'''
        if self.end_date and date.today() > self.end_date:
            return True
        return False

class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['order']

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, default='')
    content = models.TextField(blank=True, null=True)
    
    order = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    @property
    def embed_url(self):
        '''
        Gera o link de embed para YouTube e Vimeo.
        Se for Panda Video ou outro player direto, retorna o link original
        '''

        if not self.video_url:
            return ''
        
        url = self.video_url.strip()

        youtube_regex = r'(?:https?:\/\/)?(?:www\.|m\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/|live\/))([\w-]{11})(?:\S+)?'
        yt_match = re.search(youtube_regex, url)
        if yt_match:
            return f'https://www.youtube.com/embed/{yt_match.group(1)}'
        
        vimeo_regex = r'(?:https?:\/\/)?(?:www\.)?(?:vimeo\.com\/|player\.vimeo\.com\/video\/)(\d+)'
        vm_match = re.search(vimeo_regex, url)
        if vm_match:
            return f'https://player.vimeo.com/video/{vm_match.group(1)}'
        
        return url

class LessonMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials')

    file = models.FileField(upload_to='lessons/materials')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class LessonProgress(models.Model):

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')

    is_completed = models.BooleanField(default=False)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f'{self.student.email} - {self.lesson.title} - {'Concluído' if self.is_completed else 'Pendente'}'
    
    def mark_as_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

    def mark_as_peding(self):
        self.is_completed = False
        self.completed_at = None
        self.save()


class LessonComment(models.Model):

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lessons_comments')

    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comentário de {self.author.nome} na aula {self.lesson.title}'


class SuportTicket(models.Model):

    class Categories(models.TextChoices):
        DUVIDAS = 'duvidas', 'Dúvidas de Uso e Configuração'
        BUGS = 'bugs', 'Problemas Técnicos e Bugs'
        FINANCEIRO = 'financeiro', 'Financeiro e Faturamento'
        CONTA = 'conta', 'Gestão de Conta e Acessos'
        SUGESTOES = 'sugestoes', 'Sugestões de Melhoria'

    class Status(models.TextChoices):
        ABERTO = 'aberto', 'Aberto'
        EM_ANDAMENTO = 'em_andamento', 'Em andamento'
        RESOLVIDO = 'resolvido', 'Resolvido'

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tickets')
    assunto = models.CharField(max_length=100)
    categoria = models.CharField(
        max_length=100,
        choices=Categories.choices,
        )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ABERTO,
    )
    detalhes = models.TextField()
    media_ticket = models.FileField(upload_to='tickets/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket de Suporte'
        verbose_name_plural = 'Tickets de Suporte'

    def __str__(self):
        return f'[{self.get_status_display()}] {self.assunto}'


class TicketResponse(models.Model):
    ticket = models.ForeignKey(SuportTicket, on_delete=models.CASCADE, related_name='respostas')
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='respostas_tickets')
    mensagem = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Resposta'
        verbose_name_plural = 'Respostas'

    def __str__(self):
        return f'Resposta de {self.autor.email} em {self.created_at:%d/%m/%Y %H:%M}'
