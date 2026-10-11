from django.contrib import admin
from .models import Project, Comment, Milestone, TermsAndConditions


def approve_projects(modeladmin, request, queryset):
    updated_count = queryset.update(status=True)
    modeladmin.message_user(request, f"{updated_count} projects successfully approved.")

approve_projects.short_description = "Approve selected projects"


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'status', 'stage', 'posted_by', 'location', 'budget', 'end_date')
    list_filter = ('status', 'stage', 'location')
    search_fields = ('project_name', 'description')
    list_select_related = ('posted_by',)
    filter_horizontal = ('skills',)
    inlines = [MilestoneInline]

    # Add the custom action to the actions list
    actions = [approve_projects]

admin.site.register(Project, ProjectAdmin)

# Customize the fields shown in the list view
class CommetAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'state', 'proposed_price', 'date_added')
    list_filter = ('state',)
    list_select_related = ('post',)
    readonly_fields = ('token',)

admin.site.register(Comment, CommetAdmin)
admin.site.register(TermsAndConditions)
