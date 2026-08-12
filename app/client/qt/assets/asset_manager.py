from pathlib import Path
import json
import threading
from urllib.parse import quote
from urllib.request import Request, urlopen

from PySide6.QtCore import QObject, Signal, QStandardPaths, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from app.shared.card_catalog import CardCatalog
from .providers import ScryfallProvider


class AssetManager(QObject):
    image_ready = Signal(str, str, QPixmap)
    image_failed = Signal(str, str)
    _fallback_result = Signal(str, str, object, str)

    def __init__(self, catalog, cache_dir=None, provider=None, network=None, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.cache_dir = Path(cache_dir) if cache_dir else Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)) / "MTGNP" / "cards"
        self.memory = {}
        self._pending = {}
        self._failed = set()
        self.network = network or QNetworkAccessManager(self)
        self.provider = provider or ScryfallProvider(self.network, self)
        self.provider.resolved.connect(self._download)
        self.provider.failed.connect(self._failed_image)
        self._fallback_result.connect(self._on_fallback_result)

    def key(self, card_id, variant="art"):
        return CardCatalog.base_card_id(card_id), variant

    def request(self, card_id, variant="art"):
        base, variant = self.key(card_id, variant)
        key = (base, variant)
        if key in self.memory:
            self.image_ready.emit(base, variant, self.memory[key]); return
        path = self._path(base, variant)
        if path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.memory[key] = pixmap; self.image_ready.emit(base, variant, pixmap); return
            path.unlink(missing_ok=True)
        if key in self._pending or key in self._failed: return
        self._pending[key] = True
        data = self.catalog.get_card_data(base) or {}
        name = data.get("name", base.replace("_", " ").title())
        self.provider.resolve(base, name, variant)

    def _path(self, base, variant):
        directory = self.cache_dir / variant
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{base}.png"

    def _download(self, base, variant, url):
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"MTGNP-DLSU/1.0")
        request.setRawHeader(b"Accept", b"image/*,*/*;q=0.8")
        reply = self.network.get(request)
        reply.finished.connect(lambda: self._on_download(reply, base, variant))

    def _on_download(self, reply, base, variant):
        key = (base, variant); self._pending.pop(key, None)
        error = reply.errorString() if hasattr(reply, "errorString") else "unknown error"
        if reply.error():
            print(f"[QT ASSET] image download failed for {base}: {error}")
            self._failed_image(base, variant)
            reply.deleteLater(); return
        pixmap = QPixmap(); pixmap.loadFromData(bytes(reply.readAll()))
        if pixmap.isNull():
            print(f"[QT ASSET] invalid image data for {base}")
            self._failed_image(base, variant)
        else:
            self.memory[key] = pixmap
            try: pixmap.save(str(self._path(base, variant)))
            except OSError: pass
            self.image_ready.emit(base, variant, pixmap)
            print(f"[QT ASSET] loaded {base} {variant}")
        reply.deleteLater()

    def _failed_image(self, base, variant):
        if (base, variant) in self._pending:
            data = self.catalog.get_card_data(base) or {}
            name = data.get("name", base.replace("_", " ").title())
            print(f"[QT ASSET] Qt lookup failed for {name}, using HTTPS fallback")
            threading.Thread(target=self._fallback_worker, args=(base, variant, name), daemon=True).start()

    def _fallback_worker(self, base, variant, name):
        try:
            headers = {"User-Agent": "MTGNP-DLSU/1.0", "Accept": "application/json"}
            with urlopen(Request("https://api.scryfall.com/cards/named?exact=" + quote(name), headers=headers), timeout=10) as response:
                images = json.loads(response.read()).get("image_uris", {})
            url = images.get("normal") or images.get("png") or images.get("large")
            with urlopen(Request(url, headers={"User-Agent": "MTGNP-DLSU/1.0", "Accept": "image/*"}), timeout=15) as response:
                payload = response.read()
            self._fallback_result.emit(base, variant, payload, "")
        except Exception as error:
            self._fallback_result.emit(base, variant, b"", str(error))

    def _on_fallback_result(self, base, variant, payload, error):
        if error:
            print(f"[QT ASSET] fallback failed {base}: {error}")
            self._pending.pop((base, variant), None); self._failed.add((base, variant)); self.image_failed.emit(base, variant); return
        pixmap = QPixmap()
        if not pixmap.loadFromData(payload) or pixmap.isNull():
            self._pending.pop((base, variant), None); self.image_failed.emit(base, variant); return
        self.memory[(base, variant)] = pixmap
        try: pixmap.save(str(self._path(base, variant)))
        except OSError: pass
        self._pending.pop((base, variant), None)
        print(f"[QT ASSET] loaded {base} from Scryfall")
        self.image_ready.emit(base, variant, pixmap)

    def prefetch(self, card_ids, variant="art"):
        for card_id in {CardCatalog.base_card_id(item) for item in card_ids}: self.request(card_id, variant)
