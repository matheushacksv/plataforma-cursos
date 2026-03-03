from django.contrib import admin
from .models import SuportTicket, TicketResponse


class TicketResponseInline(admin.StackedInline):
    model = TicketResponse
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('mensagem', 'created_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.autor = request.user
        super().save_model(request, obj, form, change)


@admin.register(SuportTicket)
class SuportTicketAdmin(admin.ModelAdmin):
    list_display = ('assunto', 'usuario', 'categoria_display', 'status', 'created_at')
    list_filter = ('status', 'categoria', 'created_at')
    search_fields = ('assunto', 'usuario__email', 'detalhes')
    readonly_fields = ('usuario', 'assunto', 'categoria', 'detalhes', 'media_ticket', 'created_at')
    list_editable = ('status',)
    list_per_page = 20
    inlines = [TicketResponseInline]

    def categoria_display(self, obj):
        return obj.get_categoria_display()
    categoria_display.short_description = 'Categoria'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TicketResponse) and not instance.pk:
                instance.autor = request.user
            instance.save()
        formset.save_m2m()
