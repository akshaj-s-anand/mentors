from django.urls import path
from home.views import HomeView,TearmsAndConditionsView, EnrollView, AboutImageView, ContactView

app_name = 'home'

urlpatterns = [
    path('', HomeView.as_view(), name = 'home'),
    path('terms-and-conditions/', TearmsAndConditionsView.as_view(), name= 'tearms_and_conditions'),
    path('enroll/', EnrollView.as_view(), name='enroll'),
    path('about/', AboutImageView.as_view(), name = 'about'),
    path('contact/', ContactView.as_view(), name= 'contact'),
]
