from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaigns'
    
    def ready(self):
        import campaigns.signals  # Adjust path to your app name
