from django.conf import settings


def static_asset_version(_request):
    return {"STATIC_ASSET_VERSION": getattr(settings, "STATIC_ASSET_VERSION", "1")}
