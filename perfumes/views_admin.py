from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Perfume, Marca, Calificacion, ListaDeseos, HistorialVisualizacion
from django.contrib.auth.models import User

def es_admin(user):
    return user.is_authenticated and user.is_staff

def admin_required(view_func):
    decorated = login_required(user_passes_test(es_admin, login_url='/login/')(view_func))
    return decorated

@admin_required
def panel_dashboard(request):
    context = {
        'total_perfumes': Perfume.objects.count(),
        'perfumes_activos': Perfume.objects.filter(activo=True).count(),
        'total_marcas': Marca.objects.filter(activo=True).count(),
        'total_usuarios': User.objects.count(),
        'total_deseos': ListaDeseos.objects.count(),
        'total_calificaciones': Calificacion.objects.count(),
        'perfumes_sin_stock': Perfume.objects.filter(stock=0, activo=True).count(),
        'ultimos_usuarios': User.objects.order_by('-date_joined')[:5],
        'perfumes_destacados': Perfume.objects.filter(destacado=True, activo=True).count(),
        'titulo': 'Panel de Administración'
    }
    return render(request, 'perfumes/admin/dashboard.html', context)

# ── PERFUMES ────────────────────────────────────────────────────────────────

@admin_required
def admin_perfumes(request):
    perfumes = Perfume.objects.select_related('marca').order_by('-fecha_creacion')
    marcas = Marca.objects.filter(activo=True)
    
    # Filtros
    marca_id = request.GET.get('marca')
    activo = request.GET.get('activo')
    busqueda = request.GET.get('q')
    
    if marca_id:
        perfumes = perfumes.filter(marca_id=marca_id)
    if activo == '1':
        perfumes = perfumes.filter(activo=True)
    elif activo == '0':
        perfumes = perfumes.filter(activo=False)
    if busqueda:
        perfumes = perfumes.filter(nombre__icontains=busqueda)
    
    context = {
        'perfumes': perfumes,
        'marcas': marcas,
        'titulo': 'Gestión de Perfumes'
    }
    return render(request, 'perfumes/admin/perfumes_lista.html', context)

@admin_required
def admin_perfume_nuevo(request):
    marcas = Marca.objects.filter(activo=True)
    if request.method == 'POST':
        try:
            perfume = Perfume(
                nombre=request.POST['nombre'],
                marca_id=request.POST['marca'],
                sexo=request.POST['sexo'],
                tamaño=request.POST['tamaño'],
                precio=request.POST['precio'],
                stock=request.POST['stock'],
                descripcion=request.POST.get('descripcion', ''),
                activo='activo' in request.POST,
                destacado='destacado' in request.POST,
            )
            if 'imagen' in request.FILES:
                perfume.imagen = request.FILES['imagen']
            perfume.save()
            messages.success(request, f'✅ Perfume "{perfume.nombre}" creado correctamente')
            return redirect('perfumes:admin_perfumes')
        except Exception as e:
            messages.error(request, f'❌ Error al crear: {e}')
    
    context = {'marcas': marcas, 'titulo': 'Nuevo Perfume', 'accion': 'Crear'}
    return render(request, 'perfumes/admin/perfume_form.html', context)

@admin_required
def admin_perfume_editar(request, perfume_id):
    perfume = get_object_or_404(Perfume, id=perfume_id)
    marcas = Marca.objects.filter(activo=True)
    
    if request.method == 'POST':
        try:
            perfume.nombre = request.POST['nombre']
            perfume.marca_id = request.POST['marca']
            perfume.sexo = request.POST['sexo']
            perfume.tamaño = request.POST['tamaño']
            perfume.precio = request.POST['precio']
            perfume.stock = request.POST['stock']
            perfume.descripcion = request.POST.get('descripcion', '')
            perfume.activo = 'activo' in request.POST
            perfume.destacado = 'destacado' in request.POST
            if 'imagen' in request.FILES:
                perfume.imagen = request.FILES['imagen']
            perfume.save()
            messages.success(request, f'✅ Perfume "{perfume.nombre}" actualizado')
            return redirect('perfumes:admin_perfumes')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar: {e}')
    
    context = {'perfume': perfume, 'marcas': marcas, 'titulo': 'Editar Perfume', 'accion': 'Guardar'}
    return render(request, 'perfumes/admin/perfume_form.html', context)

@admin_required
@require_POST
def admin_perfume_eliminar(request, perfume_id):
    perfume = get_object_or_404(Perfume, id=perfume_id)
    nombre = perfume.nombre
    perfume.delete()
    messages.success(request, f'🗑️ Perfume "{nombre}" eliminado')
    return redirect('perfumes:admin_perfumes')

@admin_required
@require_POST
def admin_perfume_toggle(request, perfume_id):
    perfume = get_object_or_404(Perfume, id=perfume_id)
    perfume.activo = not perfume.activo
    perfume.save()
    return JsonResponse({'success': True, 'activo': perfume.activo})

# ── MARCAS ───────────────────────────────────────────────────────────────────

@admin_required
def admin_marcas(request):
    marcas = Marca.objects.annotate_perfumes() if hasattr(Marca, 'annotate_perfumes') else Marca.objects.all()
    marcas = Marca.objects.order_by('nombre')
    context = {'marcas': marcas, 'titulo': 'Gestión de Marcas'}
    return render(request, 'perfumes/admin/marcas_lista.html', context)

@admin_required
def admin_marca_nueva(request):
    if request.method == 'POST':
        try:
            marca = Marca(
                nombre=request.POST['nombre'],
                descripcion=request.POST.get('descripcion', ''),
                activo='activo' in request.POST,
            )
            if 'logo' in request.FILES:
                marca.logo = request.FILES['logo']
            marca.save()
            messages.success(request, f'✅ Marca "{marca.nombre}" creada')
            return redirect('perfumes:admin_marcas')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    return render(request, 'perfumes/admin/marca_form.html', {'titulo': 'Nueva Marca', 'accion': 'Crear'})

@admin_required
def admin_marca_editar(request, marca_id):
    marca = get_object_or_404(Marca, id=marca_id)
    if request.method == 'POST':
        try:
            marca.nombre = request.POST['nombre']
            marca.descripcion = request.POST.get('descripcion', '')
            marca.activo = 'activo' in request.POST
            if 'logo' in request.FILES:
                marca.logo = request.FILES['logo']
            marca.save()
            messages.success(request, f'✅ Marca "{marca.nombre}" actualizada')
            return redirect('perfumes:admin_marcas')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    return render(request, 'perfumes/admin/marca_form.html', {'marca': marca, 'titulo': 'Editar Marca', 'accion': 'Guardar'})

@admin_required
@require_POST
def admin_marca_eliminar(request, marca_id):
    marca = get_object_or_404(Marca, id=marca_id)
    nombre = marca.nombre
    marca.delete()
    messages.success(request, f'🗑️ Marca "{nombre}" eliminada')
    return redirect('perfumes:admin_marcas')