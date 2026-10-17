from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QPushButton, QScrollArea, QStackedWidget, QTextEdit,
    QLineEdit, QInputDialog, QMessageBox, QVBoxLayout, QWidget,
)

from app.client.qt.dialogs import CardChoiceDialog, MulliganDialog, TriggerChoiceDialog
from app.client.qt.presenter import GamePresenter
from app.client.pdu_dispatcher import PduDispatcher
from app.client.deck_builder import DEFAULT_DECKS
from app.shared.card_catalog import CardCatalog
from app.client.qt.assets import AssetManager
from app.client.qt.widgets import ZoneWidget, CardInspector
from app.client.qt.widgets import CardWidget
from app.client.qt.theme import STITCH_THEME

CATALOG_PATH = Path(__file__).resolve().parents[2] / "shared" / "card_catalog.json"


class MainWindow(QMainWindow):
    """Thread-safe Qt shell: dispatcher updates ClientState, then emits a refresh signal."""

    state_updated_signal = Signal()

    def __init__(self, state, dispatcher: PduDispatcher, parent=None):
        super().__init__(parent)
        self._ensure_rendering_fonts()
        self.state = state
        self.dispatcher = dispatcher
        self.catalog = CardCatalog(CATALOG_PATH)
        self.asset_manager = AssetManager(self.catalog, parent=self)
        self.presenter = GamePresenter(state, self.catalog)
        self._choice_dialog_open = False
        self._trigger_dialog_open = False
        self._selected_attackers = []
        self._mulligan_count = 0
        self._mulligan_hand_ids = None
        self._mulligan_waiting = False
        self._mulligan_kept = False
        self._last_phase = None
        self._ready_sent = False
        self.setWindowTitle(f"MTGNP 1.0 Client — Player: {state.pid}")
        self.resize(1510, 900)
        self.setMinimumSize(1120, 730)
        self._build_ui()
        self.state_updated_signal.connect(self.refresh_ui)
        self.refresh_ui()

    @staticmethod
    def _ensure_rendering_fonts():
        """Recover legible text when headless Qt exposes no system fonts.

        Normal desktops already have font families; no fonts are bundled or
        installed, and the fallback is skipped on those systems.
        """
        if QFontDatabase.families():
            return
        for filename in ("segoeui.ttf", "georgia.ttf", "arial.ttf"):
            font_path = Path("C:/Windows/Fonts") / filename
            if font_path.is_file():
                QFontDatabase.addApplicationFont(str(font_path))

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(76)
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(28, 8, 28, 8)
        emblem = QLabel("A")
        emblem.setAlignment(Qt.AlignCenter)
        emblem.setFixedSize(46, 46)
        emblem.setStyleSheet("color:#f2ca50; font-family:Georgia; font-size:29px; font-weight:700; background:#332b1c; border:1px solid #a48a48; border-radius:12px;")
        header_row.addWidget(emblem)
        brand_column = QVBoxLayout()
        brand_column.setSpacing(0)
        brand = QLabel("Aetherium Codex")
        brand.setObjectName("Brand")
        brand_column.addWidget(brand)
        version = QLabel("MTGNP 1.0  ·  NETWORK DUEL")
        version.setObjectName("BrandAccent")
        brand_column.addWidget(version)
        header_row.addLayout(brand_column)
        header_row.addStretch(1)
        active_view = QLabel("BATTLEFIELD")
        active_view.setObjectName("HeaderActive")
        header_row.addWidget(active_view)
        header_row.addSpacing(28)
        status_column = QVBoxLayout()
        status_column.setSpacing(5)
        self.status_label = QLabel("Phase: LOBBY | Turn: 0")
        self.life_label = QLabel("Life Totals — You: 20 | Opponent: 20")
        self.status_label.setObjectName("Status")
        self.life_label.setObjectName("Life")
        self.status_label.setAlignment(Qt.AlignRight)
        self.life_label.setAlignment(Qt.AlignRight)
        status_column.addWidget(self.status_label)
        status_column.addWidget(self.life_label)
        header_row.addLayout(status_column)
        outer.addWidget(header)
        self.pages = QStackedWidget()
        outer.addWidget(self.pages, 1)
        self._build_connection_page()
        self._build_lobby_page()
        self._build_mulligan_page()
        self._build_game_page()
        self.setStyleSheet(STITCH_THEME)

    def _build_connection_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(34, 32, 34, 32)
        layout.setSpacing(24)
        hero = QFrame()
        hero.setObjectName("HeroArt")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(42, 42, 42, 40)
        hero_layout.addWidget(self._label("WELCOME TO THE BATTLEFIELD", "Eyebrow"))
        hero_layout.addStretch(2)
        insignia = QLabel("♛")
        insignia.setStyleSheet("font-size:100px; color:#d48e4b;")
        insignia.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(insignia)
        hero_title = QLabel("MAGIC  •  THE GATHERING")
        hero_title.setStyleSheet("font-family:Georgia; font-size:31px; font-weight:700; color:#fff0d6;")
        hero_title.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(self._label("A two-player, turn-based duel of spells and strategy.", "Caption"), alignment=Qt.AlignCenter)
        hero_layout.addStretch(3)
        hero_layout.addWidget(self._label("MTGNP 1.0   /   ONLINE DUEL", "Eyebrow"))
        layout.addWidget(hero, 3)
        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(28, 30, 28, 30)
        panel_layout.setSpacing(18)
        panel_layout.addWidget(self._label("01  /  LAUNCH & CONNECT", "Eyebrow"))
        panel_layout.addWidget(self._label("Enter the arena", "PageTitle"))
        panel_layout.addWidget(self._label("Choose your deck and connect to a game server.", "Caption"))
        box = QGroupBox("CONNECTION DETAILS")
        form = QFormLayout(box)
        form.setSpacing(14)
        self.host_edit = QLineEdit("127.0.0.1"); self.port_edit = QLineEdit("4444")
        self.name_edit = QLineEdit(self.state.pid)
        self.deck_combo = QComboBox()
        self.deck_combo.addItems([f"{name} Deck" for name in DEFAULT_DECKS])
        form.addRow("Server Address", self.host_edit); form.addRow("Port", self.port_edit)
        form.addRow("Player Name", self.name_edit); form.addRow("Deck", self.deck_combo)
        panel_layout.addWidget(box)
        self.connect_btn = QPushButton("CONNECT TO SERVER  →")
        self.connect_btn.setObjectName("Primary")
        self.connect_btn.setMinimumHeight(48)
        self.connect_btn.clicked.connect(self.connect_to_server)
        panel_layout.addWidget(self.connect_btn)
        self.connection_error = QLabel("")
        self.connection_error.setObjectName("Notice")
        self.connection_error.setWordWrap(True)
        panel_layout.addWidget(self.connection_error)
        panel_layout.addStretch(1)
        panel_layout.addWidget(self._label("TCP / IPv4  •  DEFAULT PORT 4444", "Caption"))
        layout.addWidget(panel, 2)
        self.pages.addWidget(page)

    def _build_lobby_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(42, 30, 42, 30)
        layout.setSpacing(15)
        layout.addWidget(self._label("02  /  LOBBY", "Eyebrow"))
        self.lobby_title = self._label("Prepare for battle", "PageTitle")
        layout.addWidget(self.lobby_title)
        self.lobby_status = self._label("Waiting for opponent...", "Instruction")
        layout.addWidget(self.lobby_status)
        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 22, 20, 22)
        panel_layout.setSpacing(18)
        panel_layout.addWidget(self._label("Connected to game server  •  2 PLAYER MATCH", "Eyebrow"))
        row = QHBoxLayout()
        row.setSpacing(18)
        local_plate, self.local_lobby_name, self.local_lobby_state = self._lobby_player_panel("YOU", True)
        opponent_plate, self.opponent_lobby_name, self.opponent_lobby_state = self._lobby_player_panel("OPPONENT", False)
        row.addWidget(local_plate)
        row.addWidget(opponent_plate)
        panel_layout.addLayout(row)
        panel_layout.addWidget(self._label("Both players must signal READY to begin the opening hand.", "Caption"))
        layout.addWidget(panel, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.ready_btn = QPushButton("●  READY")
        self.ready_btn.setObjectName("Keep")
        self.ready_btn.setMinimumWidth(175)
        self.ready_btn.clicked.connect(self.send_ready)
        self.leave_btn = QPushButton("LEAVE LOBBY")
        self.leave_btn.setObjectName("Danger")
        self.leave_btn.clicked.connect(self.close_connection)
        buttons.addWidget(self.ready_btn)
        buttons.addWidget(self.leave_btn)
        layout.addLayout(buttons)
        self.pages.addWidget(page)

    def _build_mulligan_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 34)
        layout.setSpacing(14)
        layout.addWidget(self._label("03  /  MULLIGAN DECISION", "Eyebrow"))
        layout.addWidget(self._label("Your opening hand", "PageTitle"))
        self.mulligan_status = QLabel("Keep this hand, or mulligan for a new hand.")
        self.mulligan_status.setObjectName("Instruction")
        layout.addWidget(self.mulligan_status)
        hand_panel = QFrame()
        hand_panel.setObjectName("Playmat")
        hand_layout = QVBoxLayout(hand_panel)
        hand_layout.setContentsMargins(16, 20, 16, 20)
        self.mulligan_cards = ZoneWidget("OPENING HAND  (7)", asset_manager=self.asset_manager, card_size=(127, 178))
        self.mulligan_cards.card_clicked.connect(self._on_mulligan_card_clicked)
        self.mulligan_cards.inspect_requested.connect(self.inspect_card)
        hand_layout.addWidget(self.mulligan_cards)
        self.mulligan_selection_hint = self._label("Click a card to select it for the bottom of your library.", "Caption")
        hand_layout.addWidget(self.mulligan_selection_hint)
        layout.addWidget(hand_panel, 1)
        # Keep the authoritative physical-ID selection model for mulligan requests.
        self.mulligan_hand = QListWidget()
        self.mulligan_hand.setSelectionMode(QListWidget.MultiSelection)
        self.mulligan_hand.itemSelectionChanged.connect(self._sync_mulligan_art_selection)
        self.mulligan_hand.hide()
        layout.addWidget(self.mulligan_hand)
        row = QHBoxLayout()
        row.addStretch(1)
        self.keep_btn = QPushButton("KEEP HAND")
        self.keep_btn.setObjectName("Keep")
        self.keep_btn.setMinimumWidth(180)
        self.keep_btn.clicked.connect(self.on_keep)
        self.mull_btn = QPushButton("MULLIGAN"); self.mull_btn.setObjectName("Danger"); self.mull_btn.clicked.connect(self.on_mulligan)
        self.mull_btn.setMinimumWidth(180)
        row.addWidget(self.keep_btn); row.addWidget(self.mull_btn)
        row.addStretch(1)
        layout.addLayout(row)
        self.pages.addWidget(page)

    @staticmethod
    def _label(text, role):
        label = QLabel(text)
        label.setObjectName(role)
        return label

    def _lobby_player_panel(self, label, is_local):
        plate = QFrame()
        plate.setObjectName("PlayerPlate")
        column = QVBoxLayout(plate)
        column.setContentsMargins(20, 22, 20, 22)
        column.addWidget(self._label(label, "Eyebrow"))
        card_back = QLabel("✦\nMTGNP")
        card_back.setAlignment(Qt.AlignCenter)
        card_back.setFixedSize(130, 178)
        card_back.setStyleSheet(
            "background:qradialgradient(cx:0.5,cy:0.4,radius:0.8,fx:0.5,fy:0.4,"
            "stop:0 #425431,stop:0.65 #172c24,stop:1 #0b1519);"
            "border:5px solid #876743; border-radius:9px;"
            "color:#e7c58e; font-family:Georgia; font-size:19px; font-weight:700;"
        )
        column.addWidget(card_back, alignment=Qt.AlignHCenter)
        name = self._label(self.state.pid if is_local else "Awaiting player", "PlayerName")
        name.setAlignment(Qt.AlignHCenter)
        column.addWidget(name)
        status = self._label("NOT READY" if is_local else "WAITING...", "Instruction")
        status.setAlignment(Qt.AlignHCenter)
        column.addWidget(status)
        return plate, name, status

    def _on_mulligan_card_clicked(self, _card_id):
        selected_ids = set(self.mulligan_cards.selected_card_ids())
        for index in range(self.mulligan_hand.count()):
            item = self.mulligan_hand.item(index)
            item.setSelected(item.text() in selected_ids)

    def _sync_mulligan_art_selection(self):
        selected = set(self._mulligan_cards_selected())
        for card in self.mulligan_cards.findChildren(CardWidget):
            is_selected = card.card.card_id in selected
            card.setProperty("selected", is_selected)
            card.setStyleSheet(CardWidget.SELECTED if is_selected else CardWidget.NORMAL)
        self.mulligan_selection_hint.setText(
            f"{len(selected)} selected  •  {self._mulligan_count} card(s) required to bottom"
        )

    def _mulligan_cards_selected(self):
        return [self.mulligan_hand.item(i).text() for i in range(self.mulligan_hand.count()) if self.mulligan_hand.item(i).isSelected()]

    def _build_game_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        board = QHBoxLayout()
        board.setSpacing(10)

        rail = QFrame()
        rail.setObjectName("ArcaneRail")
        rail.setFixedWidth(224)
        phase_layout = QVBoxLayout(rail)
        phase_layout.setContentsMargins(14, 16, 14, 12)
        phase_layout.setSpacing(5)
        portrait = QLabel("A")
        portrait.setObjectName("ArchmagePortrait")
        portrait.setFixedSize(88, 88)
        portrait.setAlignment(Qt.AlignCenter)
        phase_layout.addWidget(portrait, alignment=Qt.AlignHCenter)
        self.rail_player_name = self._label(self.state.pid, "RailPlayerName")
        self.rail_player_name.setAlignment(Qt.AlignCenter)
        phase_layout.addWidget(self.rail_player_name)
        rank = self._label("PLANESWALKER  ·  CONNECTED", "RailRank")
        rank.setAlignment(Qt.AlignCenter)
        phase_layout.addWidget(rank)
        phase_layout.addSpacing(10)
        phase_layout.addWidget(self._label("TURN SEQUENCE", "Eyebrow"))
        self.phase_turn_label = self._label("Turn 1", "SectionTitle")
        phase_layout.addWidget(self.phase_turn_label)
        phase_layout.addSpacing(4)
        phases = (
            ("UNTAP", "Untap"), ("UPKEEP", "Upkeep"), ("DRAW", "Draw"),
            ("PRECOMBAT_MAIN", "Main (1)"), ("BEGIN_COMBAT", "Begin Combat"),
            ("DECLARE_ATTACKERS", "Attackers"), ("DECLARE_BLOCKERS", "Blockers"),
            ("FIRST_STRIKE_DAMAGE", "First Strike"), ("ASSIGN_DAMAGE_ORDER", "Damage Order"),
            ("COMBAT_DAMAGE", "Combat Damage"), ("END_OF_COMBAT", "End Combat"),
            ("POSTCOMBAT_MAIN", "Main (2)"), ("END", "End"), ("CLEANUP", "Cleanup"),
        )
        self.phase_items = {}
        for code, title in phases:
            label = self._label("  " + title, "PhaseIdle")
            label.setMinimumHeight(19)
            self.phase_items[code] = label
            phase_layout.addWidget(label)
        phase_layout.addStretch(1)
        self.side_cast_btn = QPushButton("CAST SPELL")
        self.side_cast_btn.setObjectName("Primary")
        self.side_cast_btn.setMinimumHeight(45)
        self.side_cast_btn.clicked.connect(self.on_cast_spell_clicked)
        phase_layout.addWidget(self.side_cast_btn)
        phase_layout.addWidget(self._label("●  LIVE NETWORK DUEL", "RailRank"))
        board.addWidget(rail)

        playmat = QFrame()
        playmat.setObjectName("Playmat")
        mat_layout = QVBoxLayout(playmat)
        mat_layout.setContentsMargins(18, 10, 18, 10)
        mat_layout.setSpacing(7)
        opponent_plate = QFrame()
        opponent_plate.setObjectName("PlayerPlate")
        opponent_row = QHBoxLayout(opponent_plate)
        opponent_row.setContentsMargins(12, 4, 12, 4)
        opponent_avatar = self._label("OP", "AvatarRed")
        opponent_avatar.setFixedSize(40, 40)
        opponent_avatar.setAlignment(Qt.AlignCenter)
        opponent_row.addWidget(opponent_avatar)
        opponent_labels = QVBoxLayout()
        opponent_labels.setSpacing(0)
        self.opponent_info = self._label("Opponent", "PlayerName")
        self.opponent_meta = self._label("Hand: —    Library: —", "Caption")
        opponent_labels.addWidget(self.opponent_info)
        opponent_labels.addWidget(self.opponent_meta)
        opponent_row.addLayout(opponent_labels, 1)
        self.opponent_health = self._label("♥ 20", "Health")
        opponent_row.addWidget(self.opponent_health)
        mat_layout.addWidget(opponent_plate)

        self.opp_battlefield_list = ZoneWidget(
            "OPPONENT BATTLEFIELD", asset_manager=self.asset_manager,
            card_size=(100, 140), compact=True,
        )
        mat_layout.addWidget(self.opp_battlefield_list)
        divider = QFrame()
        divider.setObjectName("BattlefieldDivider")
        divider_layout = QHBoxLayout(divider)
        divider_layout.setContentsMargins(12, 5, 12, 5)
        divider_layout.addWidget(self._label("THE BATTLEFIELD", "Eyebrow"))
        divider_layout.addStretch()
        self.battlefield_phase = self._label("YOUR MAIN PHASE", "PhaseCurrent")
        divider_layout.addWidget(self.battlefield_phase)
        mat_layout.addWidget(divider)
        self.your_battlefield_list = ZoneWidget(
            "YOUR BATTLEFIELD", asset_manager=self.asset_manager,
            card_size=(100, 140), compact=True,
        )
        mat_layout.addWidget(self.your_battlefield_list)
        your_plate = QFrame()
        your_plate.setObjectName("PlayerPlate")
        your_row = QHBoxLayout(your_plate)
        your_row.setContentsMargins(12, 4, 12, 4)
        your_avatar = self._label("YOU", "AvatarGreen")
        your_avatar.setFixedSize(40, 40)
        your_avatar.setAlignment(Qt.AlignCenter)
        your_row.addWidget(your_avatar)
        your_labels = QVBoxLayout()
        your_labels.setSpacing(0)
        self.your_info = self._label(self.state.pid, "PlayerName")
        self.your_meta = self._label("Hand: —    Library: —", "Caption")
        your_labels.addWidget(self.your_info)
        your_labels.addWidget(self.your_meta)
        your_row.addLayout(your_labels, 1)
        self.your_health = self._label("♥ 20", "Health")
        your_row.addWidget(self.your_health)
        mat_layout.addWidget(your_plate)
        self.hand_list = ZoneWidget(
            "YOUR HAND", asset_manager=self.asset_manager,
            card_size=(100, 140), compact=True,
        )
        mat_layout.addWidget(self.hand_list)
        # At the minimum demo size, all three fixed-height card rows cannot
        # fit vertically.  Scroll the *whole* playmat instead of clipping the
        # bottom half of battlefield / hand cards.
        playmat.setMinimumHeight(mat_layout.minimumSize().height())
        self.playmat_scroll = QScrollArea()
        self.playmat_scroll.setObjectName("BattlefieldScroll")
        self.playmat_scroll.setFrameShape(QFrame.NoFrame)
        self.playmat_scroll.setWidgetResizable(True)
        self.playmat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.playmat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.playmat_scroll.setWidget(playmat)
        board.addWidget(self.playmat_scroll, 1)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(246)
        right = QVBoxLayout(sidebar)
        right.setContentsMargins(10, 11, 10, 10)
        right.setSpacing(6)
        right.addWidget(self._label("THE STACK", "SectionTitle"))
        self.stack_list = ZoneWidget(
            "TOP RESOLVES FIRST", asset_manager=self.asset_manager,
            card_size=(93, 132), compact=True,
        )
        right.addWidget(self.stack_list)
        info_panel = QFrame()
        info_panel.setObjectName("PlayerPlate")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(2)
        info_layout.addWidget(self._label("GAME INFO", "Eyebrow"))
        self.game_info_phase = self._label("Turn —", "PhaseCurrent")
        self.game_info_priority = self._label("Priority: —", "Caption")
        info_layout.addWidget(self.game_info_phase)
        info_layout.addWidget(self.game_info_priority)
        right.addWidget(info_panel)
        self.exile_list = ZoneWidget(
            "EXILE / SUSPENDED", asset_manager=self.asset_manager,
            card_size=(82, 113), compact=True,
        )
        right.addWidget(self.exile_list)

        right.addWidget(self._label("ACTIONS", "Eyebrow"))
        dock = QFrame()
        dock.setObjectName("ActionDock")
        actions = QGridLayout(dock)
        actions.setContentsMargins(6, 7, 6, 7)
        actions.setHorizontalSpacing(5)
        actions.setVerticalSpacing(5)
        self.pass_btn = QPushButton("PASS"); self.pass_btn.clicked.connect(self.on_pass_clicked)
        self.pass_btn.setToolTip("Pass priority")
        self.play_land_btn = QPushButton("LAND"); self.play_land_btn.clicked.connect(self.on_play_land_clicked)
        self.play_land_btn.setToolTip("Play a land")
        self.cast_spell_btn = QPushButton("CAST SPELL"); self.cast_spell_btn.setObjectName("Primary"); self.cast_spell_btn.clicked.connect(self.on_cast_spell_clicked)
        self.cast_spell_btn.setToolTip("Cast a spell")
        self.activate_btn = QPushButton("ACTIVATE"); self.activate_btn.clicked.connect(self.on_activate_clicked)
        self.activate_btn.setToolTip("Activate an ability")
        self.attack_btn = QPushButton("ATTACK"); self.attack_btn.clicked.connect(self.on_attack_clicked)
        self.attack_btn.setToolTip("Confirm attackers")
        self.block_btn = QPushButton("BLOCK"); self.block_btn.clicked.connect(self.on_block_clicked)
        self.block_btn.setToolTip("Confirm blockers")
        self.order_btn = QPushButton("ORDER"); self.order_btn.clicked.connect(self.on_damage_order_clicked)
        self.order_btn.setToolTip("Confirm damage order")
        self.suspend_btn = QPushButton("SUSPEND"); self.suspend_btn.clicked.connect(self.on_suspend_clicked)
        self.suspend_btn.setToolTip("Suspend a card")
        self.concede_btn = QPushButton("CONCEDE"); self.concede_btn.setObjectName("Danger"); self.concede_btn.clicked.connect(lambda: self.dispatcher.send_concede())
        self.concede_btn.setToolTip("Concede the game")
        buttons = (
            self.pass_btn, self.play_land_btn, self.cast_spell_btn,
            self.activate_btn, self.attack_btn, self.block_btn,
            self.order_btn, self.suspend_btn, self.concede_btn,
        )
        for index, button in enumerate(buttons):
            button.setMinimumHeight(33)
            button.setStyleSheet("font-size:10px; padding:5px 4px;")
            actions.addWidget(button, index // 2, index % 2)
        right.addWidget(dock)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Status / errors")
        self.log_text.setFixedHeight(52)
        right.addWidget(self.log_text)
        self.game_over_label = self._label("", "Status")
        self.game_over_label.setWordWrap(True)
        right.addWidget(self.game_over_label)
        self.rematch_btn = QPushButton("REMATCH")
        self.rematch_btn.setObjectName("Keep")
        self.rematch_btn.clicked.connect(self.send_rematch)
        right.addWidget(self.rematch_btn)
        right.addStretch(1)
        board.addWidget(sidebar)
        layout.addLayout(board, 1)
        self.action_hint = self._label("What to do: waiting for game state...", "Instruction")
        self.action_hint.setWordWrap(True)
        layout.addWidget(self.action_hint)
        for zone in (self.opp_battlefield_list, self.your_battlefield_list, self.hand_list, self.stack_list, self.exile_list):
            zone.inspect_requested.connect(self.inspect_card)
        self.pages.addWidget(page)

    def connect_to_server(self):
        try:
            self.state.pid = self.name_edit.text().strip() or self.state.pid

            connection = self.dispatcher.connection
            connection.host = self.host_edit.text().strip()
            connection.port = int(self.port_edit.text())

            connection.connect()
            connection.start_heartbeat(self.dispatcher)

            self.state.connected = True
            self.connection_error.setText("Connected to server.")
            self.connect_btn.setEnabled(False)

            self.refresh_ui()

        except (OSError, ValueError) as error:
            self.state.connected = False
            self.connection_error.setText(f"Connection failed: {error}")

    def send_ready(self):
        if self._ready_sent:
            return
        if not self.state.deck_list:
            deck_name = self.deck_combo.currentText().split()[0]
            counts = DEFAULT_DECKS.get(deck_name, {})
            deck = self.catalog.create_deck(counts)
            self.state.deck_list = [card.card_id for card in deck]
        self.dispatcher.send_player_ready()
        self._ready_sent = True
        self.lobby_status.setText("Ready. Waiting for opponent.")
        self._refresh_visuals(self.state.phase, self.state.turn, self.state.priority_holder, self.presenter.opponent_id() or "Opponent")

    def send_rematch(self):
        self.state.reset_for_lobby()
        self._mulligan_count = 0
        self._mulligan_hand_ids = None
        self._mulligan_waiting = False
        self._mulligan_kept = False
        self.dispatcher.send_player_ready()
        self._ready_sent = True

    def close_connection(self):
        self.dispatcher.connection.close()
        self.state.connected = False
        self.state.reset_for_lobby()
        self._mulligan_count = 0
        self._mulligan_hand_ids = None
        self._mulligan_waiting = False
        self._mulligan_kept = False

        self.connect_btn.setEnabled(True)
        self._ready_sent = False
        self.connection_error.setText("")

        self.refresh_ui()

    def refresh_ui(self):
        phase = self.state.phase or self.state.current_state.get("phase", "LOBBY")
        if phase == "MULLIGAN" and self._last_phase != "MULLIGAN":
            self._mulligan_count = 0
            self._mulligan_hand_ids = None
            self._mulligan_waiting = False
            self._mulligan_kept = False
        self._last_phase = phase
        turn = self.state.turn or self.state.current_state.get("turn", 0)
        holder = self.state.priority_holder or "None"
        holder_display = "YOU" if holder == self.state.pid else holder
        self.status_label.setText(f"Phase: {phase} | Turn: {turn} | Priority: {holder_display}")
        opponent = self.presenter.opponent_id() or "Opponent"
        self.life_label.setText(f"Life Totals — You ({self.state.pid}): {self.state.life_totals.get(self.state.pid, 20)} | Opponent ({opponent}): {self.state.life_totals.get(opponent, 20)}")
        if phase == "LOBBY": self.pages.setCurrentWidget(self.pages.widget(1 if self.state.connected else 0))
        elif phase == "MULLIGAN": self.pages.setCurrentWidget(self.pages.widget(2))
        elif phase == "GAME_OVER": self.pages.setCurrentWidget(self.pages.widget(3))
        elif phase in {"GAME_SETUP", "LOBBY"}: self.pages.setCurrentWidget(self.pages.widget(1))
        else: self.pages.setCurrentWidget(self.pages.widget(3))
        self._refresh_lists(opponent)
        self._refresh_visuals(phase, turn, holder, opponent)
        self._refresh_actions(phase)
        self._refresh_guidance(phase, holder, opponent)
        self._refresh_choice()
        self._refresh_trigger_prompt()
        info = self.state.game_over_info or {}
        self.game_over_label.setText(
            f"GAME OVER — Winner: {info.get('winner_id', '—')} | {info.get('reason', '')}"
            if phase == "GAME_OVER" else ""
        )
        self.rematch_btn.setVisible(phase == "GAME_OVER")
        if getattr(self.state, "last_error", None):
            error = self.state.last_error
            self.log_text.setPlainText(f"{error.get('code', 'ERROR')}: {error.get('message', '')}")

    def _refresh_lists(self, opponent):
        hand_ids = tuple(self.state.local_hand)
        if hand_ids != self._mulligan_hand_ids:
            self.mulligan_hand.clear()
            for card_id in hand_ids:
                self.mulligan_hand.addItem(card_id)
            self.mulligan_cards.set_cards([self.presenter.card(card_id) for card_id in hand_ids])
            self.mulligan_cards.title.setText(f"OPENING HAND  ({len(hand_ids)})")
            self._mulligan_hand_ids = hand_ids
            self._sync_mulligan_art_selection()
            if self._mulligan_waiting:
                self._mulligan_waiting = False
                self.keep_btn.setEnabled(True)
                self.mull_btn.setEnabled(True)
                required = self._mulligan_count
                self.mulligan_status.setText(
                    "Keep this hand, or mulligan again."
                    if required == 0 else
                    f"Select exactly {required} card(s) to bottom, then KEEP."
                )
        self.hand_list.set_cards([self.presenter.card(card_id) for card_id in self.state.local_hand])
        self.your_battlefield_list.set_cards([self.presenter.card(card.get("id", str(card)), tapped=bool(card.get("tapped"))) for card in self.state.battlefield.get(self.state.pid, [])])
        self.opp_battlefield_list.set_cards([self.presenter.card(card.get("id", str(card)), selectable=False) for card in self.state.battlefield.get(opponent, [])])
        stack_cards = [self.presenter.card(item.get("source", "Ability")) for item in self.state.stack]
        exile_cards = [self.presenter.card(card_id) for card_id in self.state.exile.get(self.state.pid, [])]
        self.stack_list.set_cards(stack_cards)
        self.exile_list.set_cards(exile_cards)
        # Empty public zones need only their heading; reclaiming the blank card
        # row keeps the action dock from compressing at compact window heights.
        self.stack_list.scroll.setVisible(bool(stack_cards))
        self.exile_list.scroll.setVisible(bool(exile_cards))

    def _refresh_visuals(self, phase, turn, holder, opponent):
        """Update the labels in the Stitch board without touching gameplay selection."""
        self.phase_turn_label.setText(f"Turn {turn or 1}")
        for code, label in self.phase_items.items():
            active = code == phase
            label.setObjectName("PhaseCurrent" if active else "PhaseIdle")
            label.setText(("> " if active else "  ") + label.text().lstrip("> "))
            label.style().unpolish(label)
            label.style().polish(label)
        self.battlefield_phase.setText(phase.replace("_", " ").title())
        self.game_info_phase.setText(f"Turn {turn or 1}   /   {phase.replace('_', ' ').title()}")
        self.game_info_priority.setText(f"Priority: {'You' if holder == self.state.pid else holder or 'None'}")
        self.opponent_info.setText(opponent)
        self.your_info.setText(self.state.pid)
        self.rail_player_name.setText(self.state.pid)
        self.opponent_health.setText(f"♥ {self.state.life_totals.get(opponent, 20)}")
        self.your_health.setText(f"♥ {self.state.life_totals.get(self.state.pid, 20)}")
        self.opponent_meta.setText(
            f"Hand: {self.state.hand_counts.get(opponent, '—')}   "
            f"Library: {self.state.library_counts.get(opponent, '—')}   "
            f"Grave: {len(self.state.graveyard.get(opponent, []))}"
        )
        self.your_meta.setText(
            f"Hand: {len(self.state.local_hand)}   "
            f"Library: {self.state.library_counts.get(self.state.pid, '—')}   "
            f"Grave: {len(self.state.graveyard.get(self.state.pid, []))}"
        )
        self.local_lobby_name.setText(self.state.pid)
        self.local_lobby_state.setText("● READY" if self._ready_sent else "○ NOT READY")
        self.opponent_lobby_name.setText(opponent if opponent != "Opponent" else "Awaiting player")
        self.opponent_lobby_state.setText("● CONNECTED" if opponent != "Opponent" else "○ WAITING...")
        self.ready_btn.setEnabled(not self._ready_sent)

    def inspect_card(self, card_id):
        self._inspector = CardInspector(self.presenter.card(card_id), self.asset_manager, self)
        self._inspector.show()

    def _refresh_actions(self, phase):
        usable = self.state.priority_holder == self.state.pid and self.state.priority_seq_num is not None
        self.pass_btn.setEnabled(usable or phase == "LOBBY"); self.play_land_btn.setEnabled(usable and phase in {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"} and self.state.active_player == self.state.pid and not self.state.land_played_this_turn)
        self.cast_spell_btn.setEnabled(usable); self.side_cast_btn.setEnabled(usable); self.activate_btn.setEnabled(usable)
        self.attack_btn.setEnabled(phase == "DECLARE_ATTACKERS" and self.state.active_player == self.state.pid)
        self.block_btn.setEnabled(phase == "DECLARE_BLOCKERS" and self.state.active_player != self.state.pid)
        self.order_btn.setEnabled(phase == "ASSIGN_DAMAGE_ORDER" and bool(self.state.pending_damage_orders))
        self.suspend_btn.setEnabled(usable and phase in {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"})
        self.concede_btn.setEnabled(True)
        self.play_land_btn.setToolTip("You can play a land only during your own main phase.")
        self.cast_spell_btn.setToolTip("You need priority to cast a spell.")
        self.attack_btn.setToolTip("Only the active player declares attackers.")
        self.block_btn.setToolTip("The defending player declares blockers.")

    def _refresh_guidance(self, phase, holder, opponent):
        local_active = self.state.active_player == self.state.pid
        if phase == "GAME_OVER": text = "What to do: choose REMATCH to play again using the same connection."
        elif phase == "DECLARE_ATTACKERS": text = "What to do: select your attacking creatures, then CONFIRM ATTACKERS." if local_active else f"What to do: waiting for {self.state.active_player} to declare attackers."
        elif phase == "DECLARE_BLOCKERS": text = f"What to do: waiting for {opponent} to declare blockers." if local_active else "What to do: select your blockers, then CONFIRM BLOCKERS."
        elif holder and holder != self.state.pid: text = f"What to do: waiting for {holder}."
        elif phase in {"UPKEEP", "DRAW"} and holder == self.state.pid: text = "What to do: you have priority. Usually PASS PRIORITY to continue."
        elif phase in {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"} and holder == self.state.pid and local_active:
            text = "What to do: cast a spell or PASS PRIORITY." if self.state.land_played_this_turn else "What to do: select a land to PLAY LAND, cast a spell, or PASS PRIORITY."
        elif phase in {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"} and holder == self.state.pid:
            text = f"What to do: you have priority during {self.state.active_player}'s turn. Cast an instant, activate an ability, or PASS PRIORITY."
        elif phase == "BEGIN_COMBAT" and holder == self.state.pid: text = "What to do: cast an instant, activate an ability, or PASS PRIORITY."
        else: text = "What to do: waiting for the server."
        self.action_hint.setText(text)

    def _refresh_choice(self):
        request = self.state.pending_card_choice
        if request is None or self._choice_dialog_open: return
        self._choice_dialog_open = True
        dialog = CardChoiceDialog(request, self)
        if dialog.exec(): self.dispatcher.send_card_choice_response(**dialog.result)
        self._choice_dialog_open = False

    def _refresh_trigger_prompt(self):
        request = self.state.pending_request
        if request is None or self._trigger_dialog_open:
            return
        self._trigger_dialog_open = True
        if request.get("type") == "TRIGGER_ORDER":
            ids = request.get("trigger_ids", [])
            dialog = TriggerChoiceDialog("Trigger order", "Choose a trigger to place first.", ids, self)
            if dialog.exec() and dialog.selected_option:
                ordered = [dialog.selected_option] + [item for item in ids if item != dialog.selected_option]
                self.dispatcher.send_trigger_order_response(ordered)
        elif request.get("type") == "TRIGGER_CHOICE":
            options = request.get("legal_targets", []) or ["Accept"]
            dialog = TriggerChoiceDialog("Trigger choice", request.get("effect_summary", "Choose"), options, self)
            if dialog.exec() and dialog.selected_option:
                self.dispatcher.send_trigger_choice_response(
                    request.get("trigger_id"), True,
                    dialog.selected_option if request.get("requires_target") else None,
                )
        self._trigger_dialog_open = False

    def on_pass_clicked(self):
        if self.state.phase != "LOBBY" and (self.state.priority_holder != self.state.pid or self.state.priority_seq_num is None):
            self.log_text.setPlainText("You do not currently have priority."); return
        self.dispatcher.send_priority_pass(); self.log_text.setPlainText("Priority pass submitted.")

    def on_mulligan(self):
        if self._mulligan_waiting or self._mulligan_kept:
            return
        self._mulligan_count += 1
        self._mulligan_waiting = True
        self.keep_btn.setEnabled(False)
        self.mull_btn.setEnabled(False)
        self.mulligan_status.setText("Mulligan sent. Waiting for new hand...")
        self.dispatcher.send_mulligan_choice(False, cards_to_bottom=[])

    def on_keep(self):
        if self._mulligan_waiting or self._mulligan_kept:
            return
        cards = self._mulligan_cards_selected()
        required = self._mulligan_count
        if len(cards) != required:
            self.mulligan_status.setText(
                f"Select exactly {required} card(s) to bottom before keeping."
            )
            return
        self.dispatcher.send_mulligan_choice(True, cards_to_bottom=cards)
        self.keep_btn.setEnabled(False)
        self.mull_btn.setEnabled(False)
        self._mulligan_kept = True
        self.mulligan_status.setText("Hand kept. Waiting for opponent...")
        self.lobby_status.setText("Hand kept. Waiting for opponent.")

    def on_play_land_clicked(self):
        ids = self.hand_list.selected_ids()
        if self.state.active_player != self.state.pid or self.state.phase not in {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"}:
            self.log_text.setPlainText("You can only play a land during your own main phase."); return
        if self.state.land_played_this_turn:
            self.log_text.setPlainText("You have already played a land this turn."); return
        if len(ids) != 1:
            self.log_text.setPlainText("Select a land from your hand first."); return
        data = self.catalog.get_card_data(ids[0]) or {}
        if "land" not in data.get("card_type", "").casefold():
            self.log_text.setPlainText("The selected card is not a land."); return
        self.dispatcher.send_play_land(ids[0]); self.log_text.setPlainText(f"Land play submitted: {ids[0]}.")

    def _select_target(self, card_id):
        data = self.catalog.get_card_data(card_id) or {}; base = CardCatalog.base_card_id(card_id)
        opponent = self.presenter.opponent_id()
        text = data.get("text", "").casefold()
        if base in {"counterspell", "cancel", "mana_leak", "negate"}:
            options = [str(item.get("stack_item_id")) for item in self.state.stack if item.get("item_type") == "SPELL"]
        elif "target creature" in text:
            options = [p.get("id") for pid in self.state.battlefield for p in self.state.battlefield.get(pid, []) if "creature" in (self.catalog.get_card_data(p.get("id", "")) or {}).get("card_type", "").casefold()]
        elif "target player" in text and "any target" not in text:
            options = [opponent] if opponent else []
        else:
            options = [opponent] if opponent else []
            options += [p.get("id") for pid in self.state.battlefield for p in self.state.battlefield.get(pid, []) if "creature" in (self.catalog.get_card_data(p.get("id", "")) or {}).get("card_type", "").casefold()]
        if not options:
            return []
        choice, ok = QInputDialog.getItem(self, "Select target", "Target:", options, 0, False)
        return [choice] if ok and choice else []

    def on_cast_spell_clicked(self):
        ids = self.hand_list.selected_ids()
        if not ids: self.log_text.setPlainText("Select a spell from your hand first."); return
        card_id = ids[0]; data = self.catalog.get_card_data(card_id) or {}; base = CardCatalog.base_card_id(card_id)
        if "land" in data.get("card_type", "").casefold():
            self.log_text.setPlainText("Lands are played with PLAY LAND.")
            return
        requires_target = "target" in data.get("text", "").casefold()
        targets = self._select_target(card_id) if requires_target else []
        if requires_target and not targets:
            self.log_text.setPlainText("A legal target is required.")
            return
        mode = None
        payment = {"X" if key == "Generic" else key: value for key, value in data.get("mana_cost", {}).items() if value}
        if base in {"goblin_bushwhacker", "vines_of_vastwood"}:
            kicked = QMessageBox.question(self, "Kicker", "Cast this spell kicked?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
            if kicked:
                payment = {"R": 2, "X": 1} if base == "goblin_bushwhacker" else {"G": 2}
        if base == "healing_salve":
            mode, ok = QInputDialog.getItem(self, "Healing Salve", "Mode:", ["GAIN_LIFE", "PREVENT_DAMAGE"], 0, False)
            if not ok: return
        self.dispatcher.send_cast_spell(card_id, targets=targets, mana_payment=payment, mode=mode)
        self.log_text.setPlainText(f"Spell submitted: {card_id}.")

    def on_activate_clicked(self):
        ids = self.your_battlefield_list.selected_ids()
        if ids:
            source_id = ids[0]
            data = self.catalog.get_card_data(source_id) or {}
            targets = self._select_target(source_id) if "target" in data.get("text", "").casefold() else []
            self.dispatcher.send_activate_ability(source_id, targets=targets, cost_payment={"tap": True, "mana": {}})
            self.log_text.setPlainText(f"Ability submitted: {source_id}.")
        else: self.log_text.setPlainText("Select a permanent to activate.")

    def on_attack_clicked(self):
        if self.state.phase != "DECLARE_ATTACKERS": self.log_text.setPlainText("Attackers can only be declared during DECLARE_ATTACKERS."); return
        ids = self.your_battlefield_list.selected_card_ids()
        opponent = self.presenter.opponent_id()
        self.dispatcher.send_declare_attackers([{"creature_id": card_id, "target": opponent} for card_id in ids])
        self.log_text.setPlainText("Attackers submitted.")

    def on_block_clicked(self):
        attackers = self.state.attackers or []
        options = [item.get("creature_id") for item in attackers]
        if not options:
            self.dispatcher.send_declare_blockers([])
            return
        blockers = []
        for card_id in self.your_battlefield_list.selected_ids():
            attacker, ok = QInputDialog.getItem(self, "Block attacker", "Attacker:", options, 0, False)
            if ok and attacker:
                blockers.append({"creature_id": card_id, "blocking_id": attacker})
        self.dispatcher.send_declare_blockers(blockers)

    def on_damage_order_clicked(self):
        for assignment in self.state.pending_damage_orders:
            if isinstance(assignment, dict):
                self.dispatcher.send_assign_damage_order(
                    assignment.get("attacker_id"), assignment.get("blocker_ids", [])
                )

    def on_suspend_clicked(self):
        ids = self.hand_list.selected_ids()
        if ids and CardCatalog.base_card_id(ids[0]) == "rift_bolt": self.dispatcher.send_suspend_card(ids[0], {"R": 1}); self.log_text.setPlainText("Suspend submitted.")
        else: self.log_text.setPlainText("Select Rift Bolt to suspend.")

    def closeEvent(self, event):
        self.dispatcher.connection.close()
        event.accept()
