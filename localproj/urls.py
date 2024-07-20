from django.urls import path
from localproj.views import CreateProject, AllProjectsView, ProjectDetails, add_comment

app_name = 'localproj'

urlpatterns = [
    path('create/', CreateProject.as_view(), name = 'create_project'),
    path('', AllProjectsView.as_view(), name = 'all_projects'),
    path('project/<int:pk>/', ProjectDetails.as_view(), name='project_details'),
    path('project/<int:pk>/add_comment/', add_comment, name='add_comment'),
]
