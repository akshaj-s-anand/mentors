from django.contrib import admin
from mentor.models import Mentors, Category, Specialization, Mentee, TermsAndConditions
from django.db.models import Prefetch, QuerySet


admin.site.register(Category)
admin.site.register(Specialization)
admin.site.register(Mentee)

def approve_mentors(modeladmin, request, queryset: QuerySet):
    # Update the status field to True for the selected mentors
    updated_count = queryset.update(status=True)
    # Display a success message to the admin
    modeladmin.message_user(request, f"{updated_count} mentors successfully approved.")

approve_mentors.short_description = "Approve selected mentors"


@admin.action(description='Mark as verified by Oldscool (met / checked in person)')
def mark_verified(modeladmin, request, queryset):
    updated_count = queryset.update(verified=True)
    modeladmin.message_user(request, f'{updated_count} mentors marked as verified.')


class MentorsAdmin(admin.ModelAdmin):
    model = Mentors
    filter_horizontal = ('categories', 'specializations')

    list_display = ('name', 'status', 'verified', 'premium', 'qualification', 'display_specializations')
    list_filter = ('status', 'verified', 'premium', 'locality', 'specializations')
    search_fields = ('name', 'email', 'qualification', 'specializations__specialist')

    fieldsets = (
        ('Publishing', {'fields': ('status', 'verified', 'premium')}),
        ('Profile', {'fields': (
            'name', 'headline', 'image', 'about', 'qualification', 'experience', 'date_of_birth',
            'languages', 'categories', 'specializations', 'locality',
        )}),
        ('Contact', {'fields': ('contact', 'email', 'instagram', 'linkedin', 'Facebook')}),
        ('Availability & pricing', {'fields': (
            'start_weekday', 'end_weekday', 'time_from', 'time_to', 'session_minutes',
            'free_intro', 'price_per_session',
        )}),
    )
    
    def get_queryset(self, request):
        # display_specializations would otherwise run 2 queries per row
        return super().get_queryset(request).prefetch_related(
            Prefetch('specializations', queryset=Specialization.objects.select_related('category'))
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

    actions = [approve_mentors, mark_verified]

admin.site.register(Mentors, MentorsAdmin)
admin.site.register(TermsAndConditions)