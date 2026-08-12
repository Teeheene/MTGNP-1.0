from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
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

CATALOG_PATH = Path(__file__).resolve().parents[2] / "shared" / "card_catalog.json"


class MainWindow(QMainWindow):
    """Thread-safe Qt shell: dispatcher updates ClientState, then emits a refresh signal."""

    state_updated_signal = Signal()

    def __init__(self, state, dispatcher: PduDispatcher, parent=None):
        super().__init__(parent)
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
        self.resize(1366, 820)
        self._build_ui()
        self.state_updated_signal.connect(self.refresh_ui)
        self.refresh_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        self.status_label = QLabel("Phase: LOBBY | Turn: 0")
        self.life_label = QLabel("Life Totals — You: 20 | Opponent: 20")
        self.status_label.setObjectName("Status")
        self.life_label.setObjectName("Life")
        outer.addWidget(self.status_label)
        outer.addWidget(self.life_label)
        self.pages = QStackedWidget()
        outer.addWidget(self.pages, 1)
        self._build_connection_page()
        self._build_lobby_page()
        self._build_mulligan_page()
        self._build_game_page()
        self.setStyleSheet("""
            QWidget { background:#10161d; color:#edf2f7; font-size:13px; }
            QGroupBox { border:1px solid #354352; border-radius:8px; margin-top:8px; padding:10px; }
            QGroupBox::title { subcontrol-origin:margin; left:10px; color:#e4b56a; }
            QPushButton { background:#273646; border:1px solid #506276; border-radius:6px; padding:9px 14px; }
            QPushButton:hover { background:#35506a; }
            QPushButton:disabled { background:#161d24; color:#65717d; border:1px solid #28323c; }
            QPushButton:disabled:hover { background:#161d24; color:#65717d; border:1px solid #28323c; }
            QPushButton#Primary { background:#b66a27; border-color:#e4a45c; font-weight:700; }
            QPushButton#Danger { background:#79343d; }
            QListWidget, QTextEdit, QLineEdit, QComboBox { background:#18232d; border:1px solid #354352; border-radius:5px; padding:5px; }
            QLabel#Status { color:#e4b56a; font-size:16px; font-weight:700; }
            QLabel#Life { color:#9fd6a6; font-weight:700; }
        """)

    def _build_connection_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        box = QGroupBox("1. LAUNCH / CONNECT"); form = QFormLayout(box)
        self.host_edit = QLineEdit("127.0.0.1"); self.port_edit = QLineEdit("4444")
        self.name_edit = QLineEdit(self.state.pid)
        self.deck_combo = QComboBox()
        self.deck_combo.addItems([f"{name} Deck" for name in DEFAULT_DECKS])
        form.addRow("Server host", self.host_edit); form.addRow("Port", self.port_edit)
        form.addRow("Player name", self.name_edit); form.addRow("Deck", self.deck_combo)
        layout.addWidget(box)
        self.connect_btn = QPushButton("CONNECT"); self.connect_btn.setObjectName("Primary")
        self.connect_btn.clicked.connect(self.connect_to_server); layout.addWidget(self.connect_btn)
        self.connection_error = QLabel(""); layout.addWidget(self.connection_error); layout.addStretch()
        self.pages.addWidget(page)

    def _build_lobby_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        self.lobby_title = QLabel("2. LOBBY"); layout.addWidget(self.lobby_title)
        self.lobby_status = QLabel("Waiting for opponent..."); layout.addWidget(self.lobby_status)
        row = QHBoxLayout()
        self.ready_btn = QPushButton("READY"); self.ready_btn.setObjectName("Primary"); self.ready_btn.clicked.connect(self.send_ready)
        self.leave_btn = QPushButton("LEAVE LOBBY"); self.leave_btn.setObjectName("Danger"); self.leave_btn.clicked.connect(self.close_connection)
        row.addWidget(self.ready_btn); row.addWidget(self.leave_btn); layout.addLayout(row); layout.addStretch()
        self.pages.addWidget(page)

    def _build_mulligan_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("3. MULLIGAN DECISION"))
        self.mulligan_status = QLabel("Keep this hand, or mulligan for a new hand.")
        self.mulligan_status.setObjectName("Status")
        layout.addWidget(self.mulligan_status)
        self.mulligan_hand = QListWidget(); self.mulligan_hand.setSelectionMode(QListWidget.MultiSelection); layout.addWidget(self.mulligan_hand)
        row = QHBoxLayout(); self.keep_btn = QPushButton("KEEP"); self.keep_btn.setObjectName("Primary"); self.keep_btn.clicked.connect(self.on_keep)
        self.mull_btn = QPushButton("MULLIGAN"); self.mull_btn.setObjectName("Danger"); self.mull_btn.clicked.connect(self.on_mulligan)
        row.addWidget(self.keep_btn); row.addWidget(self.mull_btn); layout.addLayout(row)
        self.pages.addWidget(page)

    def _mulligan_cards_selected(self):
        return [self.mulligan_hand.item(i).text() for i in range(self.mulligan_hand.count()) if self.mulligan_hand.item(i).isSelected()]

    def _build_game_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        board = QHBoxLayout(); left = QVBoxLayout(); right = QVBoxLayout()
        self.opponent_info = QLabel("Opponent")
        self.opp_battlefield_list = ZoneWidget("Opponent Battlefield", asset_manager=self.asset_manager)
        self.your_battlefield_list = ZoneWidget("Your Battlefield", asset_manager=self.asset_manager)
        self.hand_list = ZoneWidget("Your Hand", asset_manager=self.asset_manager)
        self.stack_list = ZoneWidget("The Stack", asset_manager=self.asset_manager)
        self.exile_list = ZoneWidget("Your Exile / Suspended Cards", asset_manager=self.asset_manager)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True)
        for widget in (self.opp_battlefield_list, self.your_battlefield_list, self.hand_list):
            left.addWidget(widget, 1)
        right.addWidget(self.stack_list, 2)
        right.addWidget(self.exile_list, 1)
        right.addWidget(QLabel("Status / Errors")); right.addWidget(self.log_text, 1)
        self.game_over_label = QLabel(""); self.game_over_label.setObjectName("Status")
        right.addWidget(self.game_over_label)
        self.rematch_btn = QPushButton("REMATCH"); self.rematch_btn.setObjectName("Primary")
        self.rematch_btn.clicked.connect(self.send_rematch); right.addWidget(self.rematch_btn)
        board.addLayout(left, 3); board.addLayout(right, 2); layout.addLayout(board, 1)
        for zone in (self.opp_battlefield_list, self.your_battlefield_list, self.hand_list, self.stack_list, self.exile_list):
            zone.inspect_requested.connect(self.inspect_card)
        actions = QHBoxLayout()
        self.pass_btn = QPushButton("PASS PRIORITY"); self.pass_btn.clicked.connect(self.on_pass_clicked)
        self.play_land_btn = QPushButton("PLAY LAND"); self.play_land_btn.clicked.connect(self.on_play_land_clicked)
        self.cast_spell_btn = QPushButton("CAST SPELL"); self.cast_spell_btn.setObjectName("Primary"); self.cast_spell_btn.clicked.connect(self.on_cast_spell_clicked)
        self.activate_btn = QPushButton("ACTIVATE"); self.activate_btn.clicked.connect(self.on_activate_clicked)
        self.attack_btn = QPushButton("CONFIRM ATTACKERS"); self.attack_btn.clicked.connect(self.on_attack_clicked)
        self.block_btn = QPushButton("CONFIRM BLOCKERS"); self.block_btn.clicked.connect(self.on_block_clicked)
        self.order_btn = QPushButton("CONFIRM ORDER"); self.order_btn.clicked.connect(self.on_damage_order_clicked)
        self.suspend_btn = QPushButton("SUSPEND"); self.suspend_btn.clicked.connect(self.on_suspend_clicked)
        self.concede_btn = QPushButton("CONCEDE"); self.concede_btn.setObjectName("Danger"); self.concede_btn.clicked.connect(lambda: self.dispatcher.send_concede())
        self.action_hint = QLabel("What to do: waiting for game state..."); self.action_hint.setObjectName("Status")
        layout.addWidget(self.action_hint)
        for button in (self.pass_btn, self.play_land_btn, self.cast_spell_btn, self.activate_btn, self.attack_btn, self.block_btn, self.order_btn, self.suspend_btn, self.concede_btn): actions.addWidget(button)
        layout.addLayout(actions); self.pages.addWidget(page)

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

    def send_rematch(self):
        self.state.reset_for_lobby()
        self._mulligan_count = 0
        self._mulligan_hand_ids = None
        self._mulligan_waiting = False
        self._mulligan_kept = False
        self.dispatcher.send_player_ready()

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
            self._mulligan_hand_ids = hand_ids
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
        self.stack_list.set_cards([self.presenter.card(item.get("source", "Ability")) for item in self.state.stack])
        self.exile_list.set_cards([self.presenter.card(card_id) for card_id in self.state.exile.get(self.state.pid, [])])

    def inspect_card(self, card_id):
        self._inspector = CardInspector(self.presenter.card(card_id), self.asset_manager, self)
        self._inspector.show()

    def _refresh_actions(self, phase):
        usable = self.state.priority_holder == self.state.pid and self.state.priority_seq_num is not None
        self.pass_btn.setEnabled(usable or phase == "LOBBY"); self.play_land_btn.setEnabled(usable and phase in {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"} and self.state.active_player == self.state.pid and not self.state.land_played_this_turn)
        self.cast_spell_btn.setEnabled(usable); self.activate_btn.setEnabled(usable)
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
