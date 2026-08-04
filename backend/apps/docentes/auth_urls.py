from django.urls import path
from . import auth_views

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),
    # path('registro/', auth_views.registro_view, name='registro'),
    path('cambiar-password/', auth_views.cambiar_password_view, name='cambiar_password'),
    path('reset-password/', auth_views.solicitar_reset_password, name='solicitar-reset'),
    path('reset-password/confirmar/', auth_views.confirmar_reset_password, name='confirmar-reset'),
]
