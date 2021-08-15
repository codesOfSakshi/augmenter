from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from . import views
app_name='rl'
urlpatterns = [

    url(r'^index', views.text_form),
    url(r'^audio', views.audio_form),
    url(r'^image', views.image_form),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
