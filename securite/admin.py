from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import IntrusImage, TentativeIntrusion, AlerteAcces, Agent


class IntrusImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'description', 'date_added')
    search_fields = ('description',)

class TentativeIntrusionAdmin(admin.ModelAdmin):
    list_display = ('id', 'capture', 'datetime', 'statut')  # Utilisation des champs corrects du modèle
    list_filter = ('statut',)  # Par exemple, tu peux filtrer par statut
    search_fields = ('statut',)

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone', 'recoit_sms', 'recoit_email')
    list_editable = ('recoit_sms', 'recoit_email')  # Doit être dans list_display
    search_fields = ('nom', 'email')  # Optionnel

    def supprimer_agents(self, request, queryset):
        queryset.delete()  # Supprime les agents sélectionnés
    supprimer_agents.short_description = "Supprimer les agents sélectionnés"

admin.site.register(IntrusImage, IntrusImageAdmin)
admin.site.register(TentativeIntrusion, TentativeIntrusionAdmin)
