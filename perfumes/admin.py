from django.contrib import admin
from .models import Marca, Perfume, Calificacion
from .emails import notificar_nuevo_perfume, notificar_promocion

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'total_perfumes')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_editable = ('activo',)
    
    def total_perfumes(self, obj):
        return obj.perfumes.count()
    total_perfumes.short_description = 'Total Perfumes'


class CalificacionInline(admin.TabularInline):
    model = Calificacion
    extra = 0
    readonly_fields = ['fecha', 'ip_usuario']
    fields = ['puntuacion', 'comentario', 'ip_usuario', 'fecha']


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'sexo', 'tamaño', 'precio', 'stock', 'activo', 'destacado', 'calificacion_promedio', 'total_calificaciones')
    list_filter = (
        'sexo',           # Filtro por sexo
        'marca',          # Filtro por marca
        'tamaño',         # Filtro por tamaño
        'activo',         # Filtro por estado activo
        'destacado',      # Filtro por destacado
        'fecha_creacion', # Filtro por fecha
    )
    search_fields = ('nombre', 'marca__nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'activo', 'destacado')
    list_per_page = 25
    inlines = [CalificacionInline]
    actions = ['notificar_usuarios', 'enviar_promocion']
    
    # Campos que se muestran al editar
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'marca', 'sexo', 'tamaño')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'stock')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'imagen')
        }),
        ('Estado', {
            'fields': ('activo', 'destacado')
        }),
    )
    
    # Filtros personalizados por rango de precio
    def get_list_filter(self, request):
        filters = list(self.list_filter)
        filters.append(PrecioRangeFilter)
        return filters
    
    def calificacion_promedio(self, obj):
        return f"{obj.calificacion_promedio} ⭐"
    calificacion_promedio.short_description = 'Calificación'
    
    def total_calificaciones(self, obj):
        return obj.total_calificaciones
    total_calificaciones.short_description = 'Nº Calificaciones'
    
    def save_model(self, request, obj, form, change):
        """Notificar cuando se crea un nuevo perfume"""
        es_nuevo = obj.pk is None
        super().save_model(request, obj, form, change)
        
        if es_nuevo and obj.activo:
            # Enviar notificación de nuevo perfume
            try:
                emails_enviados = notificar_nuevo_perfume(obj)
                self.message_user(request, f'✅ Perfume guardado. Se enviaron {emails_enviados} notificaciones por email.')
            except Exception as e:
                self.message_user(request, f'⚠️ Perfume guardado, pero hubo un error al enviar emails: {e}', level='warning')
    
    def notificar_usuarios(self, request, queryset):
        """Acción para notificar sobre perfumes seleccionados"""
        total_enviados = 0
        for perfume in queryset:
            if perfume.activo:
                enviados = notificar_nuevo_perfume(perfume)
                total_enviados += enviados
        
        self.message_user(request, f'Se enviaron {total_enviados} notificaciones sobre {queryset.count()} perfume(s).')
    notificar_usuarios.short_description = '📧 Notificar usuarios sobre perfumes seleccionados'
    
    def enviar_promocion(self, request, queryset):
        """Acción para enviar promoción sobre perfumes seleccionados"""
        perfumes_nombres = ', '.join([p.nombre for p in queryset[:3]])
        if queryset.count() > 3:
            perfumes_nombres += '...'
        
        mensaje = f"""
¡Oferta especial en perfumes seleccionados!

Tenemos promociones en: {perfumes_nombres}

¡Visita nuestra tienda y aprovecha estos precios especiales!
        """
        
        enviados = notificar_promocion(
            titulo='Ofertas Especiales',
            mensaje=mensaje,
            perfumes_ids=list(queryset.values_list('id', flat=True))
        )
        
        self.message_user(request, f'Se enviaron {enviados} emails de promoción.')
    enviar_promocion.short_description = '🎉 Enviar promoción de perfumes seleccionados'


# Filtro personalizado para rangos de precio
class PrecioRangeFilter(admin.SimpleListFilter):
    title = 'Rango de Precio'
    parameter_name = 'precio_range'
    
    def lookups(self, request, model_admin):
        return (
            ('0-50', '$0 - $50,000'),
            ('50-100', '$50,000 - $100,000'),
            ('100-200', '$100,000 - $200,000'),
            ('200+', 'Más de $200,000'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '0-50':
            return queryset.filter(precio__gte=0, precio__lt=50000)
        if self.value() == '50-100':
            return queryset.filter(precio__gte=50000, precio__lt=100000)
        if self.value() == '100-200':
            return queryset.filter(precio__gte=100000, precio__lt=200000)
        if self.value() == '200+':
            return queryset.filter(precio__gte=200000)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ['perfume', 'puntuacion', 'ip_usuario', 'fecha', 'tiene_comentario']
    list_filter = ['puntuacion', 'fecha']
    search_fields = ['perfume__nombre', 'comentario', 'ip_usuario']
    readonly_fields = ['fecha']
    date_hierarchy = 'fecha'
    
    def tiene_comentario(self, obj):
        return '✓' if obj.comentario else '✗'
    tiene_comentario.short_description = 'Comentario'


from .models import HistorialVisualizacion

@admin.register(HistorialVisualizacion)
class HistorialVisualizacionAdmin(admin.ModelAdmin):
    list_display = ['perfume', 'usuario_o_sesion', 'fecha']
    list_filter = ['fecha']
    search_fields = ['perfume__nombre', 'usuario__username', 'session_key']
    readonly_fields = ['fecha', 'usuario', 'session_key', 'perfume']
    date_hierarchy = 'fecha'
    
    def usuario_o_sesion(self, obj):
        if obj.usuario:
            return f"👤 {obj.usuario.username}"
        return f"🔑 Sesión: {obj.session_key[:8]}..."
    usuario_o_sesion.short_description = 'Usuario/Sesión'
    
    def has_add_permission(self, request):
        return False  # No permitir crear manualmente


from . import models

@admin.register(models.ListaDeseos)
class ListaDeseosAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario_str', 'perfume_str', 'fecha_agregado')
    # evitar referenciar campos desconocidos en list_filter
    list_filter = ('fecha_agregado',)
    # mantener search_fields vacío para evitar errores si las relaciones tienen otros nombres
    search_fields = ()
    ordering = ('-fecha_agregado',)

    def usuario_str(self, obj):
        # intenta distintos nombres posibles de la FK al usuario
        for attr in ('user', 'usuario', 'cliente'):
            related = getattr(obj, attr, None)
            if related:
                return getattr(related, 'username', str(related))
        return '—'
    usuario_str.short_description = 'Usuario'

    def perfume_str(self, obj):
        # intenta distintos nombres posibles de la FK al perfume/producto
        for attr in ('perfume', 'producto', 'item'):
            related = getattr(obj, attr, None)
            if related:
                return getattr(related, 'nombre', getattr(related, 'title', str(related)))
        return '—'
    perfume_str.short_description = 'Perfume'