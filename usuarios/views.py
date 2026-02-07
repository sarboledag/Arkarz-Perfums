from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Vista para registrar usuario
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


# Vista para iniciar sesión
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


# Vista para cerrar sesión
def cerrar_sesion(request):
    logout(request)
    return redirect('perfumes:home')
