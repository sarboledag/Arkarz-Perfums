from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.conf import settings

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='marcas/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'


class Perfume(models.Model):
    SEXO_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
        ('U', 'Unisex'),
    ]
    
    TAMAÑO_CHOICES = [
        ('30ml', '30ml'),
        ('50ml', '50ml'),
        ('100ml', '100ml'),
        ('150ml', '150ml'),
    ]
    
    nombre = models.CharField(max_length=200)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='perfumes')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    tamaño = models.CharField(max_length=10, choices=TAMAÑO_CHOICES, default='100ml')
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='perfumes/')
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre} ({self.sexo})"
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Perfume'
        verbose_name_plural = 'Perfumes'
    
    @property
    def disponible(self):
        return self.stock > 0 and self.activo

    @property
    def precio_con_impuesto(self):
        return self.precio * 1.21
    
    @property
    def calificacion_promedio(self):
        """Retorna el promedio de calificaciones"""
        promedio = self.calificaciones.aggregate(Avg('puntuacion'))['puntuacion__avg']
        return round(promedio, 1) if promedio else 0
    
    @property
    def total_calificaciones(self):
        """Retorna el total de calificaciones"""
        return self.calificaciones.count()


class Calificacion(models.Model):
    perfume = models.ForeignKey(Perfume, on_delete=models.CASCADE, related_name='calificaciones')
    puntuacion = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    ip_usuario = models.GenericIPAddressField()
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='calificaciones')
    
    def __str__(self):
        return f"{self.perfume.nombre} - {self.puntuacion} estrellas"
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ['perfume', 'ip_usuario']


class HistorialVisualizacion(models.Model):
    """Registra qué productos ha visto cada usuario/sesión"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='visualizaciones')
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Para usuarios no autenticados
    perfume = models.ForeignKey(Perfume, on_delete=models.CASCADE, related_name='visualizaciones')
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Visualización'
        verbose_name_plural = 'Visualizaciones'
        indexes = [
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['session_key', '-fecha']),
        ]
    
    def __str__(self):
        if self.usuario:
            return f"{self.usuario.username} vio {self.perfume.nombre}"
        return f"Sesión {self.session_key[:8]} vio {self.perfume.nombre}"


class ListaDeseos(models.Model):
    """
    Productos que el usuario ha guardado en su lista de deseos
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lista_deseos'
    )
    perfume = models.ForeignKey(
        Perfume,
        on_delete=models.CASCADE,
        related_name='en_listas_deseos'
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Lista de Deseos"
        verbose_name_plural = "Listas de Deseos"
        unique_together = ('usuario', 'perfume')  # Un usuario no puede agregar el mismo producto 2 veces
        ordering = ['-fecha_agregado']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.perfume.nombre}"

