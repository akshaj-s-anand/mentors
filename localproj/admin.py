from django.contrib import admin
from .models import Project, Comment, TermsAndConditions


def approve_projects(modeladmin, request, queryset):
    updated_count = queryset.update(approved=True)
    modeladmin.message_user(request, f"{updated_count} projects successfully approved.")

approve_projects.short_description = "Approve selected projects"

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'status', 'location', 'start_date', 'end_date', 'description')
    list_filter = ('location', 'status')
    search_fields = ('project_name',)
    
    # Add the custom action to the actions list
    actions = [approve_projects]

admin.site.register(Project, ProjectAdmin)

# Customize the fields shown in the list view
class CommetAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'date_added')

admin.site.register(Comment, CommetAdmin)
admin.site.register(TermsAndConditions)








