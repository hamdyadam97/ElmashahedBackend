from django.contrib import admin
from import_export.admin import ExportMixin, ImportExportModelAdmin
from User.models import User,Client,Diploma,ClientDiploma

# Register your models here.
admin.site.register(User)
admin.site.register(Client)



@admin.register(Diploma)
class DiplomaAdmin(ImportExportModelAdmin):
    list_display = ('name', 'date')



admin.site.register(ClientDiploma)
