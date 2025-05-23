from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Student Accounts'

    def ready(self):
        # Import signals to ensure they are connected when Django starts up.
        try:
            import accounts.signals  # noqa: F401
        except Exception:
            pass  # Signals not critical during migrations
