from django.urls import path
from . import views
from . import views_admin

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

    # ── Panel Admin personalizado ──
    path('panel/', views_admin.panel_dashboard, name='admin_dashboard'),
    path('panel/perfumes/', views_admin.admin_perfumes, name='admin_perfumes'),
    path('panel/perfumes/nuevo/', views_admin.admin_perfume_nuevo, name='admin_perfume_nuevo'),
    path('panel/perfumes/<int:perfume_id>/editar/', views_admin.admin_perfume_editar, name='admin_perfume_editar'),
    path('panel/perfumes/<int:perfume_id>/eliminar/', views_admin.admin_perfume_eliminar, name='admin_perfume_eliminar'),
    path('panel/perfumes/<int:perfume_id>/toggle/', views_admin.admin_perfume_toggle, name='admin_perfume_toggle'),
    path('panel/marcas/', views_admin.admin_marcas, name='admin_marcas'),
    path('panel/marcas/nueva/', views_admin.admin_marca_nueva, name='admin_marca_nueva'),
    path('panel/marcas/<int:marca_id>/editar/', views_admin.admin_marca_editar, name='admin_marca_editar'),
    path('panel/marcas/<int:marca_id>/eliminar/', views_admin.admin_marca_eliminar, name='admin_marca_eliminar'),
]