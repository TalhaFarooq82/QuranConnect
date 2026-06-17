from django.contrib import admin
from .models import Wallet, WalletTransaction, EscrowRecord

admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(EscrowRecord)