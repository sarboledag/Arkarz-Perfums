from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


def notificar_nuevo_perfume(perfume):
    """
    Envía notificación a todos los usuarios suscritos cuando se añade un nuevo perfume
    """
    usuarios = User.objects.filter(
        perfil__notificar_nuevos_perfumes=True,
        email__isnull=False
    ).exclude(email='')
    
    if not usuarios.exists():
        return 0
    
    subject = f'🌟 Nuevo Perfume Disponible: {perfume.nombre}'
    
    emails_enviados = 0
    for usuario in usuarios:
        message = f"""
Hola {usuario.first_name or usuario.username},

¡Tenemos un nuevo perfume en nuestra tienda!

🌸 {perfume.nombre}
🏷️ Marca: {perfume.marca.nombre}
💰 Precio: ${perfume.precio}
👤 Para: {perfume.get_sexo_display()}

{perfume.descripcion[:200] if len(perfume.descripcion) > 200 else perfume.descripcion}

Visita nuestra tienda para conocer más detalles.

Saludos,
Arkarz Perfums
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=True,
            )
            emails_enviados += 1
        except Exception as e:
            print(f"Error enviando email a {usuario.email}: {e}")
    
    return emails_enviados


def notificar_promocion(titulo, mensaje, perfumes_ids=None):
    """
    Envía notificación de promociones/descuentos a usuarios suscritos
    """
    usuarios = User.objects.filter(
        perfil__notificar_promociones=True,
        email__isnull=False
    ).exclude(email='')
    
    if not usuarios.exists():
        return 0
    
    subject = f'🎉 {titulo} - Arkarz Perfums'
    
    emails_enviados = 0
    for usuario in usuarios:
        email_message = f"""
Hola {usuario.first_name or usuario.username},

{mensaje}

Visita nuestra tienda para aprovechar estas ofertas.

Saludos,
Arkarz Perfums
        """
        
        try:
            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=True,
            )
            emails_enviados += 1
        except Exception as e:
            print(f"Error enviando email a {usuario.email}: {e}")
    
    return emails_enviados
