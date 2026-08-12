import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap

from app.client.qt.dialogs import CardChoiceDialog
from app.client.qt.main_window import CATALOG_PATH, MainWindow
from app.client.qt.presenter import GamePresenter
from app.client.state import ClientState
from app.shared.card_catalog import CardCatalog
from app.client.qt.widgets import CardWidget, ZoneWidget

app = QApplication.instance() or QApplication([])


class TestQtExtendedClient(unittest.TestCase):
    def setUp(self):
        self.state = ClientState("alice")
        self.state.life_totals = {"alice": 20, "bob": 18}
        self.dispatcher = MagicMock()
        self.window = MainWindow(self.state, self.dispatcher)

    def tearDown(self):
        self.window.close()

    def test_presenter_produces_card_view_data_and_public_exile(self):
        presenter = GamePresenter(self.state, CardCatalog(CATALOG_PATH))
        card = presenter.card("forest_001", tapped=True)
        self.assertEqual(card.name, "Forest")
        self.assertTrue(card.tapped)
        self.state.update_game_state({"phase": "PRECOMBAT_MAIN", "exile": {"alice": ["rift_bolt_001"], "bob": []}})
        self.window.refresh_ui()
        self.assertEqual(self.state.exile["alice"], ["rift_bolt_001"])
        self.assertEqual(self.window.exile_list.count(), 1)

    def test_lobby_ready_uses_catalog_deck_and_dispatcher(self):
        self.window.send_ready()
        self.assertEqual(len(self.state.deck_list), 40)
        self.dispatcher.send_player_ready.assert_called_once()

    def test_generic_choice_dialog_builds_order_and_yes_no_responses(self):
        order = CardChoiceDialog({
            "choice_type": "ORDER_CARDS", "prompt": "Order", "options": ["a", "b"],
        })
        order.list_widget.item(0).setSelected(True)
        order.list_widget.item(1).setSelected(True)
        order.yes_btn.click()
        self.assertEqual(order.result, {"ordered_cards": ["a", "b"]})

        yes_no = CardChoiceDialog({"choice_type": "YES_NO", "prompt": "Search?", "options": [True, False]})
        yes_no.yes_btn.click()
        self.assertEqual(yes_no.result, {"answer": True})

    def test_priority_action_gating_and_game_board_rendering(self):
        self.state.update_game_state({
            "phase": "PRECOMBAT_MAIN", "turn": 2, "active_player": "alice",
            "priority_holder": "alice", "life_totals": {"alice": 20, "bob": 18},
            "hand": ["forest_001"], "battlefield": {"alice": [{"id": "llanowar_elves_001"}], "bob": []},
            "stack": [], "exile": {"alice": [], "bob": []},
        })
        self.window.refresh_ui()
        self.state.priority_seq_num = 1
        self.window.refresh_ui()
        self.assertTrue(self.window.pass_btn.isEnabled())
        self.assertEqual(self.window.your_battlefield_list.count(), 1)
        self.assertIn("PRECOMBAT_MAIN", self.window.status_label.text())


    def test_connect_and_disconnect_ui_state_flow(self):
        conn = MagicMock()
        self.dispatcher.connection = conn

        self.window.connect_to_server()
        self.assertTrue(self.state.connected)
        self.assertFalse(self.window.connect_btn.isEnabled())
        self.assertEqual(self.window.connection_error.text(), "Connected to server.")
        self.assertEqual(self.window.pages.currentIndex(), 1)  # Lobby page

        self.window.close_connection()
        self.assertFalse(self.state.connected)
        self.assertTrue(self.window.connect_btn.isEnabled())
        self.assertEqual(self.window.connection_error.text(), "")
        self.assertEqual(self.window.pages.currentIndex(), 0)  # Connection page

    def test_initial_keep_sends_empty_bottom(self):
        self.state.phase = "MULLIGAN"
        self.state.mulligan_seq_num = 50
        self.state.local_hand = ["forest_001", "forest_002"]
        self.window.refresh_ui()
        self.window.keep_btn.click()
        self.dispatcher.send_mulligan_choice.assert_called_once_with(True, cards_to_bottom=[])

    def test_one_mulligan_keep_requires_one_current_card(self):
        self.state.phase = "MULLIGAN"
        self.state.mulligan_seq_num = 51
        self.state.local_hand = ["forest_001", "forest_002"]
        self.window.refresh_ui()
        self.window.mull_btn.click()
        self.dispatcher.send_mulligan_choice.assert_called_once_with(False, cards_to_bottom=[])
        self.dispatcher.reset_mock()
        self.window.state.local_hand = ["forest_003", "forest_004"]
        self.window.refresh_ui()
        self.window.mulligan_hand.item(1).setSelected(True)
        self.window.keep_btn.click()
        self.dispatcher.send_mulligan_choice.assert_called_once_with(True, cards_to_bottom=["forest_004"])
        self.assertIn("Hand kept. Waiting for opponent", self.window.mulligan_status.text())

    def test_mulligan_selection_survives_unrelated_refresh_and_invalid_count_is_visible(self):
        self.state.phase = "MULLIGAN"
        self.state.local_hand = ["forest_001", "forest_002"]
        self.window.refresh_ui()
        self.window.mulligan_hand.item(0).setSelected(True)
        self.state.last_pong_timestamp = 123
        self.window.refresh_ui()
        self.assertTrue(self.window.mulligan_hand.item(0).isSelected())
        self.window.keep_btn.click()
        self.dispatcher.send_mulligan_choice.assert_not_called()
        self.assertIn("Select exactly 0", self.window.mulligan_status.text())

    def test_full_card_art_callback_and_variant_filter(self):
        manager = MagicMock()
        card = GamePresenter(self.state, CardCatalog(CATALOG_PATH)).card("forest_001")
        widget = CardWidget(card, asset_manager=manager, variant="full")
        self.assertEqual(manager.request.call_args.args, ("forest_001", "full"))
        pixmap = QPixmap(20, 20)
        widget._on_image_ready("forest", "art", pixmap)
        self.assertEqual(widget.art_label.text(), "No artwork cached")
        widget._on_image_ready("forest", "full", pixmap)
        self.assertTrue(widget.art_label.pixmap() is not None)
        self.assertEqual(widget.art_label.text(), "")

    def test_zone_uses_horizontal_scroll_area_for_fixed_cards(self):
        catalog = CardCatalog(CATALOG_PATH)
        zone = ZoneWidget("Hand")
        cards = []
        for i in range(1, 8):
            cards.append(GamePresenter(self.state, catalog).card(f"forest_{i:03d}"))
        zone.set_cards(cards)
        self.assertEqual(zone.scroll.horizontalScrollBarPolicy().value, 0)
        self.assertEqual(zone.scroll.verticalScrollBarPolicy().value, 1)
        self.assertEqual(len(zone.findChildren(type(zone.findChildren(CardWidget)[0]))), 7)
        self.assertLessEqual(zone.sizeHint().width(), 7 * 150 + 100)

    def test_play_land_requires_active_player_and_land(self):
        self.state.phase = "PRECOMBAT_MAIN"; self.state.active_player = "bob"; self.state.priority_holder = "alice"; self.state.priority_seq_num = 4
        self.state.local_hand = ["forest_013"]
        self.window.refresh_ui(); self.assertFalse(self.window.play_land_btn.isEnabled())
        self.window.hand_list.findChildren(CardWidget)[0].mousePressEvent(None) if False else None
        self.window.on_play_land_clicked()
        self.dispatcher.send_play_land.assert_not_called()

if __name__ == "__main__":
    unittest.main()
