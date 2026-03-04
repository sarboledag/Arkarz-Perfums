from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PerfilUsuario
from perfumes.models import ListaDeseos, Calificacion

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('perfumes:home')
    else:
        form = UserCreationForm()
    return render(request, 'usuarios/registro.html', {'form': form})

def inicio_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('perfumes:home')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('perfumes:home')

@login_required
def perfil(request):
    perfil_usuario, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Actualizar teléfono
        telefono = request.POST.get('telefono', '').strip()
        perfil_usuario.telefono = telefono
        
        # Actualizar preferencias de notificaciones
        perfil_usuario.notificar_nuevos_perfumes = 'notificar_nuevos_perfumes' in request.POST
        perfil_usuario.notificar_promociones = 'notificar_promociones' in request.POST
        perfil_usuario.notificar_newsletter = 'notificar_newsletter' in request.POST
        perfil_usuario.save()
        
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('perfil')

    deseos = ListaDeseos.objects.filter(usuario=request.user).select_related('perfume')
    calificaciones = Calificacion.objects.filter(usuario=request.user).select_related('perfume').order_by('-fecha')[:5]

    context = {
        'perfil': perfil_usuario,
        'deseos': deseos,
        'calificaciones': calificaciones,
        'titulo': 'Mi Perfil - Arkarz Perfums'
    }
    return render(request, 'usuarios/perfil.html', context)