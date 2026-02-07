from django.urls import path
from . import views

app_name = 'perfumes'

urlpatterns = [
    path('', views.home, name='home'),
    path('productos/', views.productos, name='productos'),
    path('perfume/<int:perfume_id>/', views.detalle_perfume, name='detalle_perfume'),
    path('marcas/', views.marcas, name='marcas'),
    path('marca/<int:marca_id>/', views.perfumes_por_marca, name='perfumes_por_marca'),
    path('buscar/', views.buscar_perfumes_ajax, name='buscar_ajax'),
    path('contacto/', views.contacto, name='contacto'),
    path('añadir-carrito/<int:perfume_id>/', views.añadir_carrito, name='añadir_carrito'),
    path('carrito/', views.carrito, name='carrito'),
    path('carrito-json/', views.carrito_json, name='carrito_json'),
    path('remove-from-cart/<int:perfume_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('calificar/<int:perfume_id>/', views.calificar_perfume, name='calificar_perfume'),
     path('lista-deseos/', views.lista_deseos, name='lista_deseos'),
    path('lista-deseos/agregar/<int:perfume_id>/', views.agregar_a_lista_deseos, name='agregar_a_lista_deseos'),
    path('lista-deseos/eliminar/<int:perfume_id>/', views.eliminar_de_lista_deseos, name='eliminar_de_lista_deseos'),
    path('lista-deseos/contar/', views.contar_lista_deseos, name='contar_lista_deseos'),
    path('lista-deseos/anadir/<int:perfume_id>/', views.agregar_a_lista_deseos, name='lista_deseos_anadir'),
]






