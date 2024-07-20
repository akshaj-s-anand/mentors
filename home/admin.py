from django.contrib import admin
from home.models import AboutImage, Contact
from django.contrib import messages

# Register your models here.
admin.site.register(AboutImage)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'message')

    def save_model(self, request, obj, form, change):
        if not change:  # Check if this is a new record
            messages.add_message(request, messages.SUCCESS, 'A new contact has been registered.')
        super().save_model(request, obj, form, change)

admin.site.register(Contact, ContactAdmin)