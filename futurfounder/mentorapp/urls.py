from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("index", views.index, name="index"),
    path('category/<int:category_id>/', views.category_page, name='category_page'),
    path('mentor/<int:mentor_id>/', views.mentor_details_view, name='mentor_details'),
    path('all_mentors',views.all_mentors, name='all_mentors'),
     
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)