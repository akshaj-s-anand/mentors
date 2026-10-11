from django.urls import path
from mentor.views import CreateMentor, AllMentorsView, MentorDetailView, mentor_by_id

app_name = 'mentor'

urlpatterns = [
    path('create/', CreateMentor.as_view(), name = 'create_mentor'),
    path('',AllMentorsView.as_view(), name = 'all_mentor'),
    # old numeric profile links (already shared / emailed) redirect to the name-based URL
    path('mentors/<int:pk>/', mentor_by_id, name='mentor_by_id'),
    # skill landing pages, e.g. /mentor/skills/12-logo-design/ and /mentor/skills/12-logo-design/kannur/
    path('skills/<int:skill_id>-<slug:slug>/', AllMentorsView.as_view(), name='skill'),
    path('skills/<int:skill_id>-<slug:slug>/<slug:district>/', AllMentorsView.as_view(), name='skill_district'),
    # profile, e.g. /mentor/jijau-kore/ (kept last; 'create', 'skills', 'mentors' are reserved slugs)
    path('<slug:slug>/', MentorDetailView.as_view(), name='mentor_details'),
]
