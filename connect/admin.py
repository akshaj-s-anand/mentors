from django.contrib import admin

from connect.models import Booking, Message, Review


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'body', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('mentee_name', 'mentor', 'kind', 'date', 'start_time', 'status', 'created_at')
    list_filter = ('status', 'kind', 'date')
    search_fields = ('mentee_name', 'email', 'mentor__name')
    list_select_related = ('mentor',)
    readonly_fields = ('token', 'created_at', 'responded_at')
    inlines = [MessageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'rating', 'reviewer_name', 'is_public', 'created_at')
    list_filter = ('is_public', 'rating')
    list_editable = ('is_public',)
    search_fields = ('mentor__name', 'reviewer_name', 'comment')
    list_select_related = ('mentor',)
