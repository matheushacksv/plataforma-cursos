from area.views import suport_ticket, listar_tickets, ticket_detail
from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('course/<int:curso_id>/toggle/', toggle_course, name='toggle_course'),
    path('course/<int:curso_id>/', course_details, name='course_details'),
    path('course/<int:curso_id>/img/', course_img, name='course_img'),
    path('course/<int:curso_id>/del_img/', delete_course_img, name='delete_course_img'),
    path('course/<int:curso_id>/create_module/', create_module, name='create_module'),
    path('course/<int:curso_id>/create_lesson/', create_lesson, name='create_lesson'),
    path('lesson/<int:lesson_id>/', lesson_details, name='lesson_details'),
    path('course/<int:curso_id>/students/', manage_students, name='manage_students'),
    path('course/<int:curso_id>/add_student/', add_student, name='add_student'),
    path('enrollment/<int:matricula_id>/update_date/', update_end_date, name='update_end_date'),
    path('enrollment/<int:matricula_id>/change_student_status/', change_student_status, name='change_student_status'),
    path('lesson/<int:lesson_id>/toggle_lesson_status/', toggle_lesson_status, name='toggle_lesson_status'),
    path('course/<int:curso_id>/manage-curriculum/', manage_curriculum, name='manage_curriculum'),
    path('course/<int:curso_id>/update-order/', update_curriculum_order, name='update_curriculum_order'),
    path('course/<int:curso_id>/drawer/', render_drawer, name='render_drawer'),
    path('lesson/<int:lesson_id>/edit/', edit_lesson, name='edit_lesson'),
    path('lesson/<int:lesson_id>/delete/', delete_lesson, name='delete_lesson'),
    path('module/<int:module_id>/edit/', edit_module, name='edit_module'),
    path('module/<int:module_id>/delete/', delete_module, name='delete_module'),
    path('lesson/<int:lesson_id>/comment/', add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('course/<int:course_id>/delete/', delete_course, name='delete_course'),
    path('course/<int:course_id>/edit/', edit_course, name='edit_course'),
    path('search-lessons/', search_lessons, name='search_lessons'),
    path('course/<int:curso_id>/reenviar-acesso', reenviar_acesso, name='reenviar_acesso'),
    path('api/webhooks/kiwify/', webhook_kiwify, name='webhook_kiwify'),
    path('course/<int:curso_id>/import-students/', import_students, name='import_students'), 
    path('tickets/', suport_ticket, name='suport_ticket'),
    path('tickets/list/', listar_tickets, name='listar_tickets'),
    path('tickets/<int:ticket_id>/', ticket_detail, name='ticket_detail'),
]

