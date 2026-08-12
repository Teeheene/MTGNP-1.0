import json
from urllib.parse import quote

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest


class ScryfallProvider(QObject):
    """Small asynchronous Scryfall adapter; image bytes are handled by AssetManager."""
    resolved = Signal(str, str, str)
    failed = Signal(str, str)

    def __init__(self, network=None, parent=None):
        super().__init__(parent)
        self.network = network or QNetworkAccessManager(self)
        self._pending = {}

    def resolve(self, base_id, card_name, variant="art"):
        key = (base_id, variant)
        if key in self._pending:
            return
        self._pending[key] = True
        request = QNetworkRequest(QUrl("https://api.scryfall.com/cards/named?exact=" + quote(card_name)))
        request.setRawHeader(b"User-Agent", b"MTGNP-DLSU/1.0")
        request.setRawHeader(b"Accept", b"application/json;q=0.9,*/*;q=0.8")
        reply = self.network.get(request)
        reply.finished.connect(lambda: self._on_lookup(reply, base_id, variant))

    def _on_lookup(self, reply, base_id, variant):
        key = (base_id, variant)
        self._pending.pop(key, None)
        if reply.error():
            print(f"[QT ASSET] lookup failed for {base_id}: {reply.errorString()}")
            self.failed.emit(base_id, variant); reply.deleteLater(); return
        try:
            data = json.loads(bytes(reply.readAll()))
            images = data.get("image_uris", {})
            url = images.get("normal") or images.get("png") or images.get("art_crop")
            if url: self.resolved.emit(base_id, variant, url)
            else: self.failed.emit(base_id, variant)
        except (ValueError, TypeError):
            self.failed.emit(base_id, variant)
        reply.deleteLater()
