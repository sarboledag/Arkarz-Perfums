from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil y Notificaciones'
    fields = ['telefono', 'notificar_nuevos_perfumes', 'notificar_promociones', 'notificar_newsletter']


# Define un nuevo User admin
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'notificaciones_activas']
    
    def notificaciones_activas(self, obj):
        if hasattr(obj, 'perfil'):
            perfil = obj.perfil
            notif = []
            if perfil.notificar_nuevos_perfumes:
                notif.append('Nuevos')
            if perfil.notificar_promociones:
                notif.append('Promos')
            if perfil.notificar_newsletter:
                notif.append('News')
            return ', '.join(notif) if notif else 'Ninguna'
        return '-'
    notificaciones_activas.short_description = 'Notificaciones'


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'notificar_nuevos_perfumes', 'notificar_promociones', 'notificar_newsletter', 'fecha_creacion']
    list_filter = ['notificar_nuevos_perfumes', 'notificar_promociones', 'notificar_newsletter']
    search_fields = ['user__username', 'user__email', 'telefono']
    readonly_fields = ['fecha_creacion']
