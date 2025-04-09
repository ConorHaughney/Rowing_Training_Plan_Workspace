from django.contrib import admin
from .models import SheetData

@admin.register(SheetData)
class SheetDataAdmin(admin.ModelAdmin):
    list_display = ('day', 'date', 'time_session_1', 'session_1', 'time_session_2', 'session_2')
    list_filter = ('day', 'date')
    search_fields = ('day', 'session_1', 'session_2')
    date_hierarchy = 'date'
    ordering = ('-date',)
    
    # Add custom actions
    actions = ['mark_as_important']
    
    # Group fields in the edit form
    fieldsets = (
        ('Basic Information', {
            'fields': ('day', 'date')
        }),
        ('Morning Session', {
            'fields': ('time_session_1', 'session_1')
        }),
        ('Afternoon Session', {
            'fields': ('time_session_2', 'session_2')
        }),
    )
    
    def mark_as_important(self, request, queryset):
        self.message_user(request, f"{queryset.count()} records marked as important.")
    mark_as_important.short_description = "Mark selected records as important"