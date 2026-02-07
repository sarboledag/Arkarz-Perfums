from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.db.models import Q
from urllib.parse import quote
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Perfume, Marca, Calificacion, ListaDeseos
from django.contrib.auth.decorators import login_required
from .recomendaciones import obtener_recomendaciones, registrar_visualizacion, productos_similares
from decimal import Decimal

def home(request):
    # Obtener recomendaciones personalizadas (CAMBIO: limite=4)
    perfumes_recomendados = obtener_recomendaciones(request, limite=4)
    marcas = Marca.objects.filter(activo=True)
    
    context = {
        'perfumes': perfumes_recomendados,
        'marcas': marcas,
        'titulo': 'Perfumes Árabes - Arkarz Perfums',
        'es_recomendacion': True
    }
    return render(request, 'perfumes/home.html', context)


def productos(request):
    marca_id = request.GET.get('marca', '')
    sexo = request.GET.get('sexo', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    busqueda = request.GET.get('q', '')

    perfumes = Perfume.objects.filter(activo=True)
    if marca_id:
        perfumes = perfumes.filter(marca_id=marca_id)
    if sexo:
        perfumes = perfumes.filter(sexo=sexo)
    if precio_min:
        try:
            perfumes = perfumes.filter(precio__gte=float(precio_min))
        except ValueError:
            pass
    if precio_max:
        try:
            perfumes = perfumes.filter(precio__lte=float(precio_max))
        except ValueError:
            pass
    if busqueda:
        perfumes = perfumes.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(marca__nombre__icontains=busqueda)
        )

    orden = request.GET.get('orden', 'nombre')
    if orden == 'precio_asc':
        perfumes = perfumes.order_by('precio')
    elif orden == 'precio_desc':
        perfumes = perfumes.order_by('-precio')
    elif orden == 'nombre':
        perfumes = perfumes.order_by('nombre')
    elif orden == 'nuevo':
        perfumes = perfumes.order_by('-id')

    paginator = Paginator(perfumes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    marcas = Marca.objects.filter(activo=True)
    context = {
        'page_obj': page_obj,
        'perfumes': page_obj,
        'marcas': marcas,
        'marca_seleccionada': marca_id,
        'sexo_seleccionado': sexo,
        'precio_min': precio_min,
        'precio_max': precio_max,
        'busqueda': busqueda,
        'orden': orden,
        'total_perfumes': perfumes.count(),
        'titulo': 'Productos - Arkarz Perfums'
    }
    return render(request, 'perfumes/productos.html', context)


def detalle_perfume(request, perfume_id):
    perfume = get_object_or_404(Perfume, id=perfume_id, activo=True)
    
    print("🔴 ANTES DE REGISTRAR VISUALIZACIÓN")
    
    # Registrar visualización
    registrar_visualizacion(request, perfume)
    
    print("🟢 DESPUÉS DE REGISTRAR VISUALIZACIÓN")
    
    # Obtener productos similares usando el sistema de recomendaciones
    perfumes_relacionados = productos_similares(perfume, limite=4)
    
    # Obtener el comentario más reciente con calificación
    comentarios_recientes = Calificacion.objects.filter(
        perfume=perfume,
        comentario__isnull=False
    ).exclude(
        comentario=''
    ).order_by('-fecha')[:1]

    context = {
        'perfume': perfume,
        'perfumes_relacionados': perfumes_relacionados,
        'comentarios_recientes': comentarios_recientes,
        'titulo': f'{perfume.nombre} - Arkarz Perfums'
    }
    return render(request, 'perfumes/detalle.html', context)


def buscar_perfumes_ajax(request):
    if request.method == 'GET':
        query = request.GET.get('q', '')
        if len(query) >= 3:
            perfumes = Perfume.objects.filter(
                Q(nombre__icontains=query) |
                Q(marca__nombre__icontains=query),
                activo=True
            )[:5]
            resultados = []
            for perfume in perfumes:
                resultados.append({
                    'id': perfume.id,
                    'nombre': perfume.nombre,
                    'marca': perfume.marca.nombre,
                    'precio': str(perfume.precio),
                    'imagen': perfume.imagen.url if perfume.imagen else '',
                    'url': f'/perfume/{perfume.id}/'
                })
            return JsonResponse({'success': True, 'resultados': resultados})
    return JsonResponse({'success': False})


def marcas(request):
    marcas = Marca.objects.filter(activo=True).order_by('nombre')
    context = {
        'marcas': marcas,
        'titulo': 'Marcas - Arkarz Perfums'
    }
    return render(request, 'perfumes/marcas.html', context)


def perfumes_por_marca(request, marca_id):
    marca = get_object_or_404(Marca, id=marca_id, activo=True)
    perfumes = Perfume.objects.filter(marca=marca, activo=True)

    paginator = Paginator(perfumes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'marca': marca,
        'page_obj': page_obj,
        'perfumes': page_obj,
        'titulo': f'Perfumes {marca.nombre} - Arkarz Perfums'
    }
    return render(request, 'perfumes/productos.html', context)


def contacto(request):
    context = {'titulo': 'Contacto - Arkarz Perfums'}
    return render(request, 'perfumes/contacto.html', context)


def carrito(request):
    carrito = request.session.get('carrito', {})
    items_carrito = []
    total = Decimal(0)
    
    for item_id, item in carrito.items():
        try:
            perfume = Perfume.objects.get(id=item_id, activo=True)
            subtotal = perfume.precio * item['cantidad']
            items_carrito.append({
                'perfume': perfume,
                'cantidad': item['cantidad'],
                'subtotal': subtotal
            })
            total += subtotal
        except Perfume.DoesNotExist:
            continue
    
    mensaje = "Hola, quisiera realizar el siguiente pedido:\n\n"
    for item in items_carrito:
        mensaje += f"- {item['perfume'].nombre} x {item['cantidad']} = ${item['subtotal']}\n"
    mensaje += f"\nTotal: ${total}"
    mensaje_codificado = quote(mensaje)
    whatsapp_numero = "573218599032"
    whatsapp_url = f"https://wa.me/{whatsapp_numero}?text={mensaje_codificado}"

    context = {
        'items_carrito': items_carrito,
        'total': total,
        'whatsapp_url': whatsapp_url,
        'titulo': 'Carrito - Arkarz Perfums'
    }
    return render(request, 'perfumes/carrito.html', context)


@require_POST
def añadir_carrito(request, perfume_id):
    perfume = get_object_or_404(Perfume, id=perfume_id, activo=True)
    carrito = request.session.get('carrito', {})

    try:
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1:
            return JsonResponse({'success': False, 'error': 'Cantidad inválida'}, status=400)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Cantidad inválida'}, status=400)

    str_id = str(perfume_id)
    if str_id in carrito:
        carrito[str_id]['cantidad'] += cantidad
    else:
        carrito[str_id] = {
            'nombre': perfume.nombre,
            'cantidad': cantidad,
            'precio': float(perfume.precio),
            'imagen': perfume.imagen.url if perfume.imagen else ''
        }
    
    request.session['carrito'] = carrito
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'message': 'Producto añadido al carrito',
        'total_items': sum(item['cantidad'] for item in carrito.values())
    })


@require_POST
def eliminar_del_carrito(request, perfume_id):
    carrito = request.session.get('carrito', {})
    str_id = str(perfume_id)
    
    if str_id in carrito:
        del carrito[str_id]
        request.session['carrito'] = carrito
        request.session.modified = True
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado del carrito'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Producto no encontrado en el carrito'
    }, status=404)


def carrito_json(request):
    carrito = request.session.get('carrito', {})
    items = []
    total_items = 0
    total_monto = Decimal(0)
    
    for pid, item in carrito.items():
        try:
            perfume = Perfume.objects.get(id=pid, activo=True)
            precio = perfume.precio
            cantidad = item['cantidad']
            subtotal = precio * cantidad
            
            items.append({
                'id': pid,
                'nombre': item['nombre'],
                'cantidad': cantidad,
                'precio': float(precio),
                'subtotal': float(subtotal),
                'imagen': item.get('imagen', '')
            })
            total_items += cantidad
            total_monto += subtotal
        except Perfume.DoesNotExist:
            continue
    
    return JsonResponse({
        'items': items,
        'total_items': total_items,
        'total_monto': float(total_monto),
    })


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_POST
def calificar_perfume(request, perfume_id):
    perfume = get_object_or_404(Perfume, id=perfume_id, activo=True)
    
    try:
        puntuacion = int(request.POST.get('puntuacion'))
        if puntuacion < 1 or puntuacion > 5:
            return JsonResponse({'success': False, 'error': 'Puntuación inválida'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Puntuación inválida'}, status=400)
    
    ip_usuario = get_client_ip(request)
    comentario = request.POST.get('comentario', '').strip()
    
    # Crear o actualizar calificación
    calificacion, created = Calificacion.objects.update_or_create(
        perfume=perfume,
        ip_usuario=ip_usuario,
        defaults={
            'puntuacion': puntuacion,
            'comentario': comentario if comentario else None
        }
    )
    
    mensaje = 'Calificación registrada' if created else 'Calificación actualizada'
    
    return JsonResponse({
        'success': True,
        'message': mensaje,
        'promedio': perfume.calificacion_promedio,
        'total': perfume.total_calificaciones
    })


# ========== LISTA DE DESEOS ==========

@login_required
def lista_deseos(request):
    """
    Muestra la lista de deseos del usuario
    """
    deseos = ListaDeseos.objects.filter(usuario=request.user).select_related('perfume', 'perfume__marca')
    
    context = {
        'deseos': deseos,
        'titulo': 'Mi Lista de Deseos - Arkarz Perfums'
    }
    return render(request, 'perfumes/lista_deseos.html', context)


@login_required
@require_POST
def agregar_a_lista_deseos(request, perfume_id):
    """
    Agrega un perfume a la lista de deseos del usuario
    """
    perfume = get_object_or_404(Perfume, id=perfume_id, activo=True)
    
    # Crear o verificar si ya existe
    lista_deseos, created = ListaDeseos.objects.get_or_create(
        usuario=request.user,
        perfume=perfume
    )
    
    if created:
        return JsonResponse({
            'success': True,
            'message': f'"{perfume.nombre}" agregado a tu lista de deseos',
            'action': 'added'
        })
    else:
        return JsonResponse({
            'success': True,
            'message': f'"{perfume.nombre}" ya está en tu lista de deseos',
            'action': 'already_exists'
        })


@login_required
@require_POST
def eliminar_de_lista_deseos(request, perfume_id):
    """
    Elimina un perfume de la lista de deseos del usuario
    """
    perfume = get_object_or_404(Perfume, id=perfume_id)
    
    try:
        lista_deseos = ListaDeseos.objects.get(usuario=request.user, perfume=perfume)
        lista_deseos.delete()
        return JsonResponse({
            'success': True,
            'message': f'"{perfume.nombre}" eliminado de tu lista de deseos',
            'action': 'removed'
        })
    except ListaDeseos.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'El producto no está en tu lista de deseos'
        }, status=404)


@login_required
def contar_lista_deseos(request):
    """
    Devuelve el número de productos en la lista de deseos (para el navbar)
    """
    count = ListaDeseos.objects.filter(usuario=request.user).count()
    return JsonResponse({'count': count})









