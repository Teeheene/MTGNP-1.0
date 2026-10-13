from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QDialog, QSizePolicy, QHBoxLayout, QScrollArea, QWidget, QLayout
from PySide6.QtGui import QPixmap
from app.shared.card_catalog import CardCatalog


class CardWidget(QFrame):
    clicked = Signal(str)
    inspect_requested = Signal(str)

    NORMAL = "QFrame#CardWidget { background:#211d17; border:1px solid #958052; border-radius:7px; }"
    SELECTED = "QFrame#CardWidget { background:#34301c; border:3px solid #f2ca50; border-radius:7px; }"
    HOVERED = "QFrame#CardWidget { background:#403520; border:2px solid #e9c349; border-radius:7px; }"

    def __init__(self, card, parent=None, asset_manager=None, variant="full", card_size=(150, 210)):
        super().__init__(parent)
        self.card = card
        self._asset_variant = variant
        self.selectable = bool(card.selectable)
        self.setCursor(Qt.PointingHandCursor if self.selectable else Qt.ArrowCursor)
        self.setProperty("selected", False)
        self.asset_manager = asset_manager
        self._asset_base = CardCatalog.base_card_id(card.card_id)
        self.setObjectName("CardWidget")
        self.setFixedSize(*card_size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(6, 5, 6, 5)
        self.name_label = QLabel(card.name)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(36)
        self.name_label.setStyleSheet("font-weight:700; color:#f6e5b5; font-family:Georgia;")
        self.card_layout.addWidget(self.name_label)
        self.art_label = QLabel("Artwork unavailable")
        self.art_label.setAlignment(Qt.AlignCenter)
        self.art_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.art_label.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4a3e2b,stop:1 #1b1a16); color:#c7bda5; border-radius:4px;")
        self.card_layout.addWidget(self.art_label, 1)
        mana = card.mana_cost if isinstance(card.mana_cost, str) else str(card.mana_cost)
        footer = f"{mana}  •  {card.card_type}"
        if card.power_toughness:
            footer += f"  •  {card.power_toughness}"
        self.footer_label = QLabel(footer)
        self.footer_label.setWordWrap(True)
        self.footer_label.setMaximumHeight(42)
        self.footer_label.setStyleSheet("color:#d1c6ad; font-size:10px;")
        self.card_layout.addWidget(self.footer_label)
        self.tapped_label = None
        if card.tapped:
            self.tapped_label = QLabel("TAPPED", alignment=Qt.AlignCenter)
            self.tapped_label.setStyleSheet("background:#725c24; color:white; font-weight:700;")
            self.card_layout.addWidget(self.tapped_label)
        self.setStyleSheet(self.NORMAL)
        self.setToolTip(f"{card.name}\n{card.card_type}\nDouble-click to inspect")
        if asset_manager:
            asset_manager.image_ready.connect(self._on_image_ready)
            asset_manager.request(card.card_id, variant)

    def _on_image_ready(self, base_id, variant, pixmap):
        if base_id != self._asset_base or variant != self._asset_variant or self.card is None: return
        self.name_label.hide()
        self.footer_label.hide()
        if self.tapped_label:
            self.tapped_label.hide()
        self.card_layout.setContentsMargins(4, 4, 4, 4)
        width, height = self.width() - 10, self.height() - 10
        self.art_label.setFixedSize(width, height)
        self.art_label.setPixmap(pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.art_label.setText("")

    def mousePressEvent(self, event):
        if self.selectable:
            self.setProperty("selected", not bool(self.property("selected")))
            self.setStyleSheet(self.SELECTED if self.property("selected") else self.NORMAL)
        self.clicked.emit(self.card.card_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.selectable or self.card:
            self.inspect_requested.emit(self.card.card_id)
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        if self.selectable and not self.property("selected"):
            self.setStyleSheet(self.HOVERED)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.property("selected"):
            self.setStyleSheet(self.NORMAL)
        super().leaveEvent(event)


class CardInspector(QDialog):
    """Large preview that never reveals identities absent from the supplied card."""
    def __init__(self, card, asset_manager=None, parent=None):
        super().__init__(parent)
        self.card = card; self.asset_manager = asset_manager
        self._full_failed = False; self._full_ready = False
        self.setWindowTitle(card.name); self.resize(420, 600)
        layout = QVBoxLayout(self)
        self.image = QLabel("No artwork cached"); self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumSize(300, 400); layout.addWidget(self.image)
        layout.addWidget(QLabel(f"{card.name}\n{card.mana_cost}\n{card.card_type}\n{getattr(card, 'rules_text', getattr(card, 'text', ''))}"))
        if asset_manager:
            asset_manager.image_ready.connect(self._on_image)
            asset_manager.image_failed.connect(self._on_failed)
            asset_manager.request(card.card_id, "full")

    def _on_image(self, base_id, variant, pixmap):
        if base_id != CardCatalog.base_card_id(self.card.card_id): return
        if variant == "full": self._full_ready = True
        if variant == "art" and not self._full_failed: return
        self.image.setPixmap(pixmap.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image.setText("")

    def _on_failed(self, base_id, variant):
        if base_id == CardCatalog.base_card_id(self.card.card_id) and variant == "full" and not self._full_ready:
            self._full_failed = True
            self.asset_manager.request(self.card.card_id, "art")


class ZoneWidget(QFrame):
    card_clicked = Signal(str)
    inspect_requested = Signal(str)

    def __init__(self, title, parent=None, asset_manager=None, card_size=(150, 210), compact=False):
        super().__init__(parent)
        self.setObjectName("ZoneWidget")
        self.card_size = card_size
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6 if compact else 10, 5, 6 if compact else 10, 6)
        self.layout.setSpacing(4)
        self.title = QLabel(title)
        self.title.setObjectName("ZoneTitle")
        self.layout.addWidget(self.title)
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setContentsMargins(8, 4, 8, 4)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.cards_host = QWidget()
        self.cards_host.setLayout(self.cards_layout)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setObjectName("CardScroll")
        self.scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scroll.setFixedHeight(card_size[1] + 23)
        self.scroll.setMinimumWidth(0)
        self.scroll.setWidget(self.cards_host)
        self.layout.addWidget(self.scroll)
        self.asset_manager = asset_manager

    def set_cards(self, cards):
        cards = list(cards)
        signature = tuple((card.card_id, card.tapped, card.selectable) for card in cards)
        if signature == getattr(self, "_signature", None):
            return
        selected = set(self.selected_card_ids())
        self._signature = signature
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for card in cards:
            widget = CardWidget(card, asset_manager=self.asset_manager, card_size=self.card_size)
            if card.card_id in selected:
                widget.setProperty("selected", True)
                widget.setStyleSheet(CardWidget.SELECTED)
            widget.clicked.connect(self.card_clicked)
            widget.inspect_requested.connect(self.inspect_requested)
            self.cards_layout.addWidget(widget)
        self.cards_host.adjustSize()

    def count(self):
        return self.cards_layout.count()

    def clear(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def addItem(self, text):
        # Compatibility no-op for legacy callers; production rendering uses CardWidget.
        return None

    def selected_card_ids(self):
        return [w.card.card_id for w in self.findChildren(CardWidget) if w.property("selected")]

    def selected_card_id(self):
        ids = self.selected_card_ids()
        return ids[0] if ids else None

    def clear_selection(self):
        for widget in self.findChildren(CardWidget):
            widget.setProperty("selected", False)
            widget.setStyleSheet(CardWidget.NORMAL)

    # Backward-compatible name used only by existing Qt action code.
    def selected_ids(self):
        return self.selected_card_ids()
