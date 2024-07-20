from django.urls import path
from mentor.views import CreateMentor, AllMentorsView, MentorDetailView

app_name = 'mentor'

urlpatterns = [
    path('create/', CreateMentor.as_view(), name = 'create_mentor'),
    path('',AllMentorsView.as_view(), name = 'all_mentor'),
    path('mentors/<int:pk>/', MentorDetailView.as_view(), name='mentor_details'),
]
