import tempfile
import unittest
import json
import ssl
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QApplication

from app.client.qt.assets.asset_manager import AssetManager
from app.client.qt.main_window import CATALOG_PATH
from app.shared.card_catalog import CardCatalog

QApplication.instance() or QApplication([])


class FakeProvider(QObject):
    resolved = Signal(str, str, str)
    failed = Signal(str, str)

    def __init__(self):
        super().__init__(); self.calls = []

    def resolve(self, base, name, variant):
        self.calls.append((base, name, variant))


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.catalog = CardCatalog(CATALOG_PATH)
        self.provider = FakeProvider()
        self.manager = AssetManager(self.catalog, cache_dir=self.tmp.name, provider=self.provider)

    def tearDown(self): self.tmp.cleanup()

    def test_physical_ids_share_base_and_provider_lookup(self):
        self.manager.request("lightning_bolt_001")
        self.manager.request("lightning_bolt_002")
        self.assertEqual(self.provider.calls, [("lightning_bolt", "Lightning Bolt", "art")])

    def test_disk_cache_hit_avoids_provider_and_corrupt_cache_is_ignored(self):
        path = Path(self.tmp.name) / "art" / "lightning_bolt.png"; path.parent.mkdir()
        pix = QPixmap(8, 8); pix.fill(QColor("red")); pix.save(str(path))
        self.manager.request("lightning_bolt_003")
        self.assertFalse(self.provider.calls)
        path.write_bytes(b"not an image")
        self.manager.memory.clear(); self.manager.request("lightning_bolt_003")
        self.assertEqual(len(self.provider.calls), 1)

    def test_remote_image_is_cached_and_emitted(self):
        self.manager.request("forest_001")
        self.assertEqual(len(self.provider.calls), 1)
        source = Path(self.tmp.name) / "source.png"
        pix = QPixmap(10, 10); pix.fill(QColor("green")); pix.save(str(source))
        # Feed a fake network reply through the manager's download completion path.
        class Reply:
            def error(self): return False
            def readAll(self): return source.read_bytes()
            def deleteLater(self): pass
        got = []
        self.manager.image_ready.connect(lambda *args: got.append(args))
        self.manager._on_download(Reply(), "forest", "art")
        self.assertTrue(got and not got[0][2].isNull())
        self.assertTrue((Path(self.tmp.name) / "art" / "forest.png").exists())

    def test_prefetch_deduplicates_physical_instances(self):
        self.manager.prefetch(["forest_001", "forest_002", "forest_003"])
        self.assertEqual(len(self.provider.calls), 1)

    def test_verified_ca_context_used_for_metadata_and_image(self):
        source = Path(self.tmp.name) / "source.png"
        pix = QPixmap(10, 10); pix.fill(QColor("green")); pix.save(str(source))
        responses = [
            json.dumps({"image_uris": {"normal": "https://img.example/forest.png"}}).encode(),
            source.read_bytes(),
        ]
        class Response:
            def __init__(self, payload): self.payload = payload
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return self.payload
        with patch("app.client.qt.assets.asset_manager.urlopen", side_effect=[Response(item) for item in responses]) as mocked:
            self.manager._fallback_worker("forest", "full", "Forest")
        self.assertEqual(self.manager.ssl_context.verify_mode, ssl.CERT_REQUIRED)
        self.assertIn("exact=Forest", mocked.call_args_list[0].args[0].full_url)
        self.assertIs(mocked.call_args_list[0].kwargs["context"], self.manager.ssl_context)
        self.assertIs(mocked.call_args_list[1].kwargs["context"], self.manager.ssl_context)
        self.assertIn(("forest", "full"), self.manager.memory)
