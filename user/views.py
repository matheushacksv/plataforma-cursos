from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from .tasks import send_password_reset_email
import secrets

def login_view(request):

    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')
    
    elif request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('password')

        user = authenticate(request, username=email, password=senha)

        if user is not None:
            login(request, user)

            resposta = HttpResponse()
            resposta['HX-Redirect'] = '/dashboard'
            return resposta
        else:
            erro_html = '<span class="text-error font-semibold">E-mail ou senha inválido</span>'
            return HttpResponse(erro_html)
        
def logout_view(request):
    logout(request)

    return redirect('login')

@login_required(login_url='/login/')
def profile_view(request):

    user = request.user

    if request.method == 'POST':
        user.nome = request.POST.get('nome', user.nome)
        user.phone = request.POST.get('phone', user.phone)

        if 'avatar' in request.FILES:
            user.avatar = request.FILES.get('avatar')

        user.save()

        return HttpResponse('''
            <div class="alert alert-success shadow-sm mt-4 animate-fade-in">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <span>Perfil atualizado com sucesso!</span>
            </div>
        ''')
    return render(request, 'profile.html', {'user': user})
        
@login_required(login_url='/login/')
def settings_view(request):
    user = request.user

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not user.check_password(old_password):
            return HttpResponse('''
                <div class="alert alert-error shadow-sm mt-4 animate-fade-in text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <span>A senha atual está incorreta.</span>
                </div>
            ''')
        
        if new_password != confirm_password:
            return HttpResponse('''
                <div class="alert alert-warning shadow-sm mt-4 animate-fade-in text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    <span>A nova senha e a confirmação não batem.</span>
                </div>           
            ''')
        
        if len(new_password) < 6:
            return HttpResponse('''
                <div class="alert alert-warning shadow-sm mt-4 animate-fade-in text-sm">
                    <span>A nova senha deve ter pelo menos 6 caracteres.</span>
                </div>
            ''')
        
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        return HttpResponse('''
            <div class="alert alert-success shadow-sm mt-4 animate-fade-in text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <span>Senha alterada com sucesso!</span>
            </div>
            <script>document.getElementById('form-password').reset();</script>
        ''')
    return render(request, 'settings.html')
                            
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email)
            senha_aleatoria = secrets.token_urlsafe(16)
            user.set_password(senha_aleatoria)
            user.save()
            send_password_reset_email.delay(user.email, senha_aleatoria)
            return HttpResponse('''
                <div class="alert alert-success shadow-sm mt-4 animate-fade-in text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <span>Senha alterada com sucesso!</span>
                </div>
                <a href="/login/" class="btn btn-info mt-4 w-full">
                    Voltar para o login
                </a>
            ''')
            
        except CustomUser.DoesNotExist:
            return HttpResponse('''
                <div class="alert alert-error shadow-sm mt-4 animate-fade-in text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <span>E-mail não encontrado.</span>
                </div>
            ''')

    return render(request, 'forgot_password.html')



