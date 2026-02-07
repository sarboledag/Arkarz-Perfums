from django.db.models import Count, Q, Avg
from collections import Counter
from .models import Perfume, HistorialVisualizacion, Calificacion, Marca


def obtener_recomendaciones(request, limite=4):  # ← CAMBIO 1: limite=4
    """
    Obtiene recomendaciones personalizadas basadas en el historial del usuario
    """
    print("🔍 Iniciando sistema de recomendaciones...")
    
    usuario = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    
    if not session_key and not usuario:
        print("⚠️ Sin sesión ni usuario - mostrando destacados")
        return Perfume.objects.filter(activo=True, destacado=True)[:limite]
    
    # Obtener historial de visualizaciones
    if usuario:
        visualizaciones = list(HistorialVisualizacion.objects.filter(usuario=usuario).select_related('perfume').order_by('-fecha')[:20])
        print(f"👤 Usuario: {usuario.username} - {len(visualizaciones)} visualizaciones")
    else:
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        visualizaciones = list(HistorialVisualizacion.objects.filter(session_key=session_key).select_related('perfume').order_by('-fecha')[:20])
        print(f"🔑 Sesión: {session_key[:8]} - {len(visualizaciones)} visualizaciones")
    
    if not visualizaciones:
        print("⚠️ Sin historial - mostrando populares")
        return obtener_mas_populares(limite)
    
    # Analizar preferencias del usuario
    perfumes_vistos_ids = [v.perfume_id for v in visualizaciones]
    perfumes_vistos = [v.perfume for v in visualizaciones]
    
    # Contar marcas y géneros más vistos
    marcas_contador = Counter([p.marca_id for p in perfumes_vistos])
    generos_contador = Counter([p.sexo for p in perfumes_vistos])
    
    marca_favorita = marcas_contador.most_common(1)[0][0] if marcas_contador else None
    genero_favorito = generos_contador.most_common(1)[0][0] if generos_contador else None
    
    if marca_favorita:
        marca_obj = Marca.objects.get(id=marca_favorita)
        print(f"⭐ Marca favorita detectada: {marca_obj.nombre}")
    if genero_favorito:
        print(f"👥 Género favorito: {dict(Perfume.SEXO_CHOICES).get(genero_favorito)}")
    
    # CAMBIO 2: Buscar productos de la marca favorita + género
    if marca_favorita:
        filtros = {
            'activo': True,
            'marca_id': marca_favorita
        }
        
        # Si hay género favorito claro, agregarlo al filtro
        if genero_favorito:
            filtros['sexo'] = genero_favorito
        
        # PRIMERO: Intentar sin los ya vistos
        recomendaciones = Perfume.objects.filter(
            **filtros
        ).exclude(
            id__in=perfumes_vistos_ids
        ).order_by('?')[:limite]  # ← Orden aleatorio para variedad
        
        # SI NO HAY SUFICIENTES: Incluir todos (incluso los ya vistos)
        if recomendaciones.count() < limite:
            print(f"⚠️ Solo {recomendaciones.count()} productos nuevos - incluyendo productos ya vistos")
            recomendaciones = Perfume.objects.filter(
                **filtros
            ).order_by('?')[:limite]
        
        if recomendaciones.exists():
            marca_obj = Marca.objects.get(id=marca_favorita)
            print(f"✅ Recomendaciones de {marca_obj.nombre}: {recomendaciones.count()} productos")
            print(f"📋 Productos recomendados: {list(recomendaciones.values_list('nombre', flat=True))}")
            return list(recomendaciones)
    
    # Si no hay marca favorita clara, usar género
    if genero_favorito:
        recomendaciones = Perfume.objects.filter(
            activo=True,
            sexo=genero_favorito
        ).exclude(
            id__in=perfumes_vistos_ids
        ).order_by('?')[:limite]  # ← Orden aleatorio
        
        print(f"✅ Recomendaciones por género: {recomendaciones.count()} productos")
        print(f"📋 Productos recomendados: {list(recomendaciones.values_list('nombre', flat=True))}")
        return list(recomendaciones)
    
    # Fallback: productos populares
    print("➡️ Usando productos populares como fallback")
    return obtener_mas_populares(limite, excluir_ids=perfumes_vistos_ids)


def obtener_mas_populares(limite=4, excluir_ids=None):  # ← CAMBIO 3: limite=4
    """
    Obtiene los productos más populares basados en visualizaciones y calificaciones
    """
    queryset = Perfume.objects.filter(activo=True)
    
    if excluir_ids:
        queryset = queryset.exclude(id__in=excluir_ids)
    
    return queryset.annotate(
        num_visualizaciones=Count('visualizaciones'),
        calificacion_avg=Avg('calificaciones__puntuacion')
    ).order_by('-num_visualizaciones', '-calificacion_avg', '-destacado')[:limite]


def registrar_visualizacion(request, perfume):
    """
    Registra que un usuario/sesión ha visto un producto
    """
    usuario = request.user if request.user.is_authenticated else None
    
    # Asegurar que existe una sesión
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Evitar duplicados recientes (últimas 24 horas)
    from django.utils import timezone
    from datetime import timedelta
    
    hace_24h = timezone.now() - timedelta(hours=24)
    
    if usuario:
        existe = HistorialVisualizacion.objects.filter(
            usuario=usuario,
            perfume=perfume,
            fecha__gte=hace_24h
        ).exists()
        
        if not existe:
            HistorialVisualizacion.objects.create(
                usuario=usuario,
                session_key=None,
                perfume=perfume
            )
            print(f"✅ Registrado: Usuario {usuario.username} vio {perfume.nombre}")
    else:
        existe = HistorialVisualizacion.objects.filter(
            session_key=session_key,
            perfume=perfume,
            fecha__gte=hace_24h
        ).exists()
        
        if not existe:
            HistorialVisualizacion.objects.create(
                usuario=None,
                session_key=session_key,
                perfume=perfume
            )
            print(f"✅ Registrado: Sesión {session_key[:8]} vio {perfume.nombre}")


def productos_similares(perfume, limite=4):
    """
    Encuentra productos similares a uno dado
    """
    return Perfume.objects.filter(
        activo=True
    ).filter(
        Q(marca=perfume.marca) | Q(sexo=perfume.sexo)
    ).exclude(
        id=perfume.id
    ).annotate(
        calificacion_avg=Avg('calificaciones__puntuacion')
    ).order_by('-calificacion_avg', '-destacado')[:limite]