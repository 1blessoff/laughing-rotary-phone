from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_defunt', 'client', 'caveau', 'statut', 'date_reservation')
    list_filter = ('statut', 'date_reservation')
    search_fields = ('nom_defunt', 'prenom_defunt', 'client__username')
    readonly_fields = ('date_reservation',)