from django.contrib import admin
from mentor.models import Mentors, Category, Specialization, Mentee, TermsAndConditions
from django.db.models import QuerySet


admin.site.register(Category)
admin.site.register(Specialization)
admin.site.register(Mentee)

def approve_mentors(modeladmin, request, queryset: QuerySet):
    # Update the status field to True for the selected mentors
    updated_count = queryset.update(status=True)
    # Display a success message to the admin
    modeladmin.message_user(request, f"{updated_count} mentors successfully approved.")

approve_mentors.short_description = "Approve selected mentors"



from django.contrib import admin
from .models import Mentors

class MentorsAdmin(admin.ModelAdmin):
    model = Mentors
    filter_horizontal = ('categories', 'specializations')

    list_display = ('name', 'status', 'qualification', 'display_specializations')
    list_filter = ('status', 'qualification', 'specializations')
    search_fields = ('name', 'qualification', 'specializations__specialist')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'contact', 'email', 'qualification', 'status', 'categories', 'specializations', 'date_of_birth', 'experience', 'start_weekday', 'end_weekday', 'time_from', 'time_to', 'image', 'instagram', 'linkedin', 'Facebook', 'locality', 'about', 'premium')
        }),
    )
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "specializations":
            kwargs["queryset"] = db_field.remote_field.model.objects.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def display_specializations(self, obj):
        return ", ".join(str(specialization) for specialization in obj.specializations.all())
    display_specializations.short_description = 'Specializations'
    
    def display_id(self, obj):
        return obj.id
    display_id.short_description = 'Mentor ID'

    actions = [approve_mentors]

admin.site.register(Mentors, MentorsAdmin)
admin.site.register(TermsAndConditions)