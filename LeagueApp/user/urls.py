from django.conf.urls import url

from . import views

app_name = 'user'
urlpatterns = [url(r'^$', views.handle_user, name='user'),
               url(r"^(?P<username>[\S .'-]+)/results/", views.results, name='results')]