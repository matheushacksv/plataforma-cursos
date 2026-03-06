from django.urls import path
from django.views.generic.base import RedirectView
from .views import login_view, logout_view, profile_view, settings_view, forgot_password_view, edit_student_email

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('forgot_password', forgot_password_view, name='forgot_password'),
    path('edit_student_email/<int:student_id>/', edit_student_email, name='edit_student_email')
]
