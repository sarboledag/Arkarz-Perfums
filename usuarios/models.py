from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    # Preferencias de notificaciones
    notificar_nuevos_perfumes = models.BooleanField(
        default=True, 
        verbose_name='Notificar nuevos perfumes',
        help_text='Recibir email cuando se agreguen nuevos perfumes'
    )
    notificar_promociones = models.BooleanField(
        default=True,
        verbose_name='Notificar promociones',
        help_text='Recibir email sobre descuentos y ofertas'
    )
    notificar_newsletter = models.BooleanField(
        default=False,
        verbose_name='Newsletter mensual',
        help_text='Recibir boletín mensual con novedades'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'


# Crear perfil automáticamente cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
