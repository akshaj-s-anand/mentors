from django.contrib import admin
from .models import Mentors, Category, Specialization, Mentee




admin.site.register(Category)
admin.site.register(Specialization)
admin.site.register(Mentee)



class MentorsAdmin(admin.ModelAdmin):
    model = Mentors
    filter_horizontal = ('categories', 'specializations')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "specializations":
            # Clear any queryset filtering for specializations
            kwargs["queryset"] = db_field.remote_field.model.objects.all()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

admin.site.register(Mentors, MentorsAdmin)




