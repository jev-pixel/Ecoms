# shop/storage_backends.py
"""
Custom Django Storage backend for Vercel Blob.
Used for MEDIA (user-uploaded product/category images) when running on
Vercel, where the container filesystem is ephemeral and can't hold uploads.
Static files still go through WhiteNoise — this is media-only.
"""
import vercel_blob
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class VercelBlobStorage(Storage):
    def _save(self, name, content):
        data = content.read()
        result = vercel_blob.put(name, data, {"access": "public", "addRandomSuffix": "true"})
        # vercel_blob returns the final pathname (with random suffix) it stored under
        self._last_url = result["url"]
        return result["pathname"]

    def _open(self, name, mode="rb"):
        raise NotImplementedError("Reading files back through Django isn't needed — served via .url()")

    def exists(self, name):
        # Vercel Blob has no cheap "does this exact key exist" check; returning
        # False lets Django always write (addRandomSuffix avoids collisions anyway).
        return False

    def url(self, name):
        # If we just saved it this request, we already have the real URL.
        if hasattr(self, "_last_url"):
            return self._last_url
        # Otherwise reconstruct from the public base URL env var (see settings).
        from django.conf import settings
        base = settings.VERCEL_BLOB_PUBLIC_BASE_URL.rstrip("/")
        return f"{base}/{name}"

    def delete(self, name):
        try:
            vercel_blob.delete(name)
        except Exception:
            pass

    def size(self, name):
        try:
            return vercel_blob.head(name).get("size", 0)
        except Exception:
            return 0