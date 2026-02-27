from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from area.models import Course, Module, Lesson, Enrollment, LessonProgress, LessonMaterial, LessonComment
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.db.models import Max
from user.models import CustomUser
from django.utils.dateparse import parse_date
from .tasks import enviar_email_1_acesso, reenviar_email_acesso
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import secrets
from django.conf import settings


@login_required(login_url='/login/')
def dashboard(request):
    if request.method == 'GET':

        matriculas = Enrollment.objects.filter(
            student=request.user,
            is_active = True
        ).select_related('course')

        return render(request, 'dashboard.html', {'matriculas': matriculas})
    
    if request.method == 'POST':

        title = request.POST.get('titulo')
        description = request.POST.get('descricao')
        image = request.FILES.get('imagem')
        categories = request.POST.getlist('categoria')
        kiwify_id = request.POST.get('id_kiwify')
        active = request.POST.get('ativo') == 'on'

        curso = Course.objects.create(
            title=title,
            image=image,
            description=description,
            categories=categories,
            kiwify_product_id=kiwify_id,
            active=active
        )

        Enrollment.objects.create(
            student=request.user,
            course=curso,
            is_active=True
        )

        response = HttpResponse()
        response['HX-Redirect'] = reverse('dashboard')

        return response

@login_required(login_url='/login/')
def toggle_course(request, curso_id):
    if request.method == 'POST' and request.user.is_staff:
        curso = get_object_or_404(Course, id=curso_id)

        curso.active = not curso.active
        curso.save()

        return HttpResponse(status=200)
    return HttpResponse('Acesso negado', status=403)

@login_required(login_url='/login/')
def course_details(request, curso_id):
    if request.method == 'GET':
        query = Course.objects.prefetch_related('modules__lessons')

        curso = get_object_or_404(query, id=curso_id)

        user = request.user

        aulas_concluidas = []

        
        aulas_concluidas = LessonProgress.objects.filter(
            student=user,
            lesson__module__course_id=curso_id,
            is_completed=True
        ).values_list('lesson_id', flat=True)

        context = {
            'curso': curso,
            'user': user,
            'aulas_concluidas': aulas_concluidas
        }

        return render(request, 'course_details.html', context)

@login_required(login_url='/login/')
def course_img(request, curso_id):
    if request.method == 'POST' and request.user.is_staff:
        curso = get_object_or_404(Course, id=curso_id)

        img = request.FILES.get('imagem')
        if img:
            curso.image = img
            curso.save()

        response = HttpResponse()
        response['HX-Refresh'] = 'true'

        return response

@login_required(login_url='/login/')
def delete_course_img(request, curso_id):
    if request.method == 'POST' and request.user.is_staff:

        curso = get_object_or_404(Course, id=curso_id)

        curso.image.delete()
        curso.save()

        response= HttpResponse()
        response['HX-Refresh'] = 'true'

        return response

@login_required(login_url='/login/')
def create_module(request, curso_id):
    if request.method == 'POST' and request.user.is_staff:
        curso = get_object_or_404(Course, id=curso_id)

        current_max = Module.objects.filter(course=curso).aggregate(Max('order'))['order__max']
        next_order = (current_max or 0) + 1

        module = Module.objects.create(
            course=curso,
            title=request.POST.get('titulo'),
            order=next_order
        )

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'gradeAtualizada'

        return response
    return HttpResponse(status=400)
    
@login_required(login_url='/login/')
def create_lesson(request, curso_id):
    if request.method == 'POST' and request.user.is_staff:
        
        modulo_id = request.POST.get('modulo_id')

        modulo = get_object_or_404(Module, id=modulo_id, course_id=curso_id)

        current_max = Lesson.objects.filter(module=modulo).aggregate(Max('order'))['order__max']
        next_order = (current_max or 0) + 1

        lesson = Lesson.objects.create(
            module=modulo,
            title=request.POST.get('titulo'),
            description=request.POST.get('descricao'),
            video_url=request.POST.get('video_url'),
            content=request.POST.get('content'),            
            order=next_order
        )

        arquivos = request.FILES.getlist('attachments')

        for arquivo in arquivos:
            LessonMaterial.objects.create(
                lesson=lesson,
                file=arquivo
            )

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'gradeAtualizada'

        return response
    return HttpResponse(status=400)
    
@login_required(login_url='/login/')
def lesson_details(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    curso = lesson.module.course

    is_completed = False

    progresso = LessonProgress.objects.filter(student=request.user, lesson=lesson).first()

    if progresso and progresso.is_completed:
        is_completed = True

    context = {
        'lesson': lesson,
        'is_completed': is_completed,
        'curso': curso
    }

    if 'HX-Request' in request.headers:
        return render(request, 'partials/_lesson_details.html', context)
    
    context['aulas_concluidas'] = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=curso,
        is_completed=True
    ).values_list('lesson_id', flat=True)

    context['lesson_ativa'] = lesson

    return render(request, 'course_details.html', context)

@login_required(login_url='/login/')
def manage_students(request, curso_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    curso = get_object_or_404(Course, id=curso_id)

    matriculas = Enrollment.objects.filter(course=curso).order_by('-start_date')

    context = {
        'curso': curso,
        'matriculas': matriculas
    }

    return render(request, 'partials/_manage_students.html', context)

@login_required(login_url='/login/')
def add_student(request, curso_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    curso = get_object_or_404(Course, id=curso_id)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        end_date_str = request.POST.get('end_date')

        end_date = parse_date(end_date_str) if end_date_str else None

        if email:
            user, created = CustomUser.objects.get_or_create(
                email=email            
            )

            if created:
                senha_aleatoria = secrets.token_urlsafe(8)
                user.set_password(senha_aleatoria)
                user.save()

            curso.students.add(user)

            Enrollment.objects.update_or_create(
                student=user,
                course=curso,
                defaults={
                    'end_date': end_date,
                    'is_active': True
                }
            )

            if created:
                print('url:', settings.CELERY_BROKER_URL)
                enviar_email_1_acesso.delay(email, senha_aleatoria)

    matriculas = Enrollment.objects.filter(course=curso). order_by('-start_date')

    context = {
        'curso': curso,
        'matriculas': matriculas
    }

    return render(request, 'partials/_manage_students.html', context)

@login_required(login_url='/login/')
def update_end_date(request, matricula_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    if request.method == 'POST':
        matricula = get_object_or_404(Enrollment, id=matricula_id)

        nova_data_str = request.POST.get('end_date')

        matricula.end_date = parse_date(nova_data_str) if nova_data_str else None
        matricula.save()

        curso = matricula.course

        matriculas = Enrollment.objects.filter(course=curso).order_by('-start_date')

        context = {
            'curso': curso,
            'matriculas': matriculas
        }

        return render(request, 'partials/_manage_students.html', context)
    
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def change_student_status(request, matricula_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    if request.method == 'POST':
        matricula = get_object_or_404(Enrollment, id=matricula_id)

        matricula.is_active = not matricula.is_active
        matricula.save()

        curso = matricula.course

        matriculas = Enrollment.objects.filter(course=curso).order_by('-start_date')

        context = {
            'curso': curso,
            'matriculas': matriculas
        }

        return render(request, 'partials/_manage_students.html', context)
    
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def reenviar_acesso(request, curso_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    if request.method == 'POST':
        
        student_id = request.POST.get('student_id')

        aluno = get_object_or_404(CustomUser, id=student_id)

        senha_aleatoria = secrets.token_urlsafe(8)
        aluno.set_password(senha_aleatoria)
        aluno.save()

        reenviar_email_acesso.delay(aluno.email, senha_aleatoria)

        return render(request, 'partials/_toast_sucesso.html')
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def toggle_lesson_status(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)

        progresso, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )

        if progresso.is_completed:
            progresso.mark_as_peding()
            is_completed = False
        else:
            progresso.mark_as_completed()
            is_completed = True

        context = {
            'lesson': lesson,
            'is_completed': is_completed,
            'is_htmx_post': True
        }

        response = render(request, 'partials/_lesson_button.html', context)
        return response
    
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def update_curriculum_order(request, curso_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    if request.method == 'POST':
        dados_json = request.POST.get('nova_estrutura', '[]')
        estrutura = json.loads(dados_json)

        for mod_data in estrutura:
            mod_id = mod_data['id']
            mod_order = mod_data['order']

            Module.objects.filter(id=mod_id).update(order=mod_order)

            for aula_data in mod_data['aulas']:
                aula_id = aula_data['id']
                aula_order = aula_data['order']

                Lesson.objects.filter(id=aula_id).update(
                    order=aula_order,
                    module_id=mod_id
                )

        response = HttpResponse(status=200)
        response['HX-Trigger'] = 'gradeAtualizada'

        return response

    return HttpResponse(status=400)

@login_required(login_url='/login/')
def manage_curriculum(request, curso_id):
    if not request.user.is_staff:
        return HttpResponse('Acesso negado', status=403)
    
    curso = get_object_or_404(Course, id=curso_id)

    modulos = curso.modules.all().order_by('order')

    context = {
        'curso': curso,
        'modulos': modulos,
    }

    return render(request, 'partials/_manage_curriculum.html', context)

@login_required(login_url='/login/')
def render_drawer(request, curso_id):
    curso = get_object_or_404(Course, id=curso_id)

    return render(request, 'partials/_drawer.html', {'curso': curso})

@login_required(login_url='/login/')
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'POST' and request.user.is_staff:
        lesson.title = request.POST.get('titulo')
        lesson.description = request.POST.get('descricao')
        lesson.video_url = request.POST.get('video_url')
        lesson.content = request.POST.get('content')
        lesson.save()

        arquivos = request.FILES.getlist('attachments')
        for arquivo in arquivos:
            LessonMaterial.objects.create(lesson=lesson, file=arquivo)

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'gradeAtualizada'
        return response
    return render(request, 'partials/_edit_lesson_modal.html', {'aula': lesson})

@login_required(login_url='/login/')
def delete_lesson(request, lesson_id):
    if request.method == 'POST' and request.user.is_staff:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        lesson.delete()

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'gradeAtualizada'
        return response
    
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def edit_module(request, module_id):
    modulo = get_object_or_404(Module, id=module_id)

    if request.method == 'POST' and request.user.is_staff:
        modulo.title = request.POST.get('titulo')
        modulo.save()

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'gradeAtualizada'
        return response
    return render(request, 'partials/_edit_module_modal.html', {'modulo': modulo})

@login_required(login_url='/login/')
def delete_module(request, module_id):
    if request.method == 'POST' and request.user.is_staff:
        modulo = get_object_or_404(Module, id=module_id)
        modulo.delete()

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'gradeAtualizada'
        return response
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def add_comment(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'POST':
        body = request.POST.get('body')
        if body and body.strip():
            LessonComment.objects.create(
                lesson=lesson,
                author=request.user,
                body=body
            )

    return render(request, 'partials/_comments_section.html', {'lesson': lesson})

@login_required(login_url='/login/')
def delete_comment(request, comment_id):
    comment = get_object_or_404(LessonComment, id=comment_id)
    lesson = comment.lesson

    if request.method == 'POST' and request.user.is_staff:
        comment.delete()

    return render(request, 'partials/_comments_section.html', {'lesson': lesson})

@login_required(login_url='/login/')
def delete_course(request, course_id):
    if request.method == 'POST' and request.user.is_staff:
        course = get_object_or_404(Course, id=course_id)

        course.delete()

        return HttpResponse('')
    return HttpResponse(status=403)

@login_required(login_url='/login/')
def edit_course(request, course_id):
    curso = get_object_or_404(Course, id=course_id)

    if request.method == 'POST' and request.user.is_staff:
        curso.title = request.POST.get('title')
        curso.description = request.POST.get('description')
        curso.kiwify_product_id = request.POST.get('id_kiwify')
        curso.save()

        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response
    return render(request, 'partials/_edit_course_modal.html', {'curso': curso})

@login_required(login_url='/login/')
def search_lessons(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return HttpResponse('')
    
    if request.user.is_staff:
        lessons = Lesson.objects.filter(
            title__icontains=query
        ).select_related('module__course')[:8]
    else:
        cursos_ativos_ids = Enrollment.objects.filter(
            student=request.user,
            is_active=True
        ).values_list('course_id', flat=True)

        lessons = Lesson.objects.filter(
            module__course_id__in=cursos_ativos_ids,
            title__icontains=query
        ).select_related('module__course')[:8]

    return render(request, 'partials/_search_results.html', {'lessons': lessons, 'query': query})

@csrf_exempt
@require_POST
def webhook_kiwify(request):
    try:
        data = json.loads(request.body)

        if isinstance(data, list) and 'body' in data[0]:
            payload = data[0]['body']
        else:
            payload = data

        event_type = payload.get('webhook_event_type')
        status = payload.get('order_status')

        if event_type == 'order_approved' or status == 'paid':
            customer_data = payload.get('Customer', {})
            product_data = payload.get('Product', {})

            email = customer_data.get('email')
            full_name = customer_data.get('full_name', 'Aluno')
            kiwify_id = product_data.get('product_id')

            if not email or not kiwify_id:
                return JsonResponse({'erro': 'Faltam dados do aluno ou produto'}, status=400)
            
            user, created = CustomUser.objects.get_or_create(email=email)

            if created:
                user.first_name = full_name.split()[0]

                if hasattr(user, 'username'):
                    user.username = email

                senha_temporaria = secrets.token_urlsafe(8)
                user.set_password(senha_temporaria)
                user.save()

                enviar_email_1_acesso.delay(email, senha_temporaria)

            try:
                curso = Course.objects.get(kiwify_product_id=kiwify_id)
            except Course.DoesNotExist:
                return JsonResponse({'erro': 'Curso não encontrado no sistema'}, status=404)
            
            Enrollment.objects.get_or_create(
                student=user,
                course=curso,
                defaults={'is_active': True}
            )
            return JsonResponse({'status': 'matricula_criada_com_sucesso'}, status=200)
        return JsonResponse({'status': 'evento_ignorado'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Formato inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


