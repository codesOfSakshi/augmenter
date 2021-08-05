from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from . import views
app_name='rl'
urlpatterns = [

    url(r'^index', views.my_form_post),
    url(r'^audio', views.audio_form),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
