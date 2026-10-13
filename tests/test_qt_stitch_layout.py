"""Layout regressions for the themed production board."""

import os
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.client.qt.main_window import MainWindow
from app.client.qt.widgets import CardWidget
from app.client.state import ClientState


app = QApplication.instance() or QApplication([])


class TestStitchBoardLayout(unittest.TestCase):
    def setUp(self):
        self.state = ClientState("alice")
        self.window = MainWindow(self.state, MagicMock())

    def tearDown(self):
        self.window.close()

    def _populate_board(self):
        self.state.phase = "PRECOMBAT_MAIN"
        self.state.turn = 6
        self.state.active_player = "alice"
        self.state.priority_holder = "alice"
        self.state.local_hand = [
            "forest_001", "grizzly_bears_001", "lightning_bolt_001",
            "counterspell_001", "dark_ritual_001", "forest_002",
        ]
        self.state.battlefield = {
            "alice": [{"id": "forest_003"}, {"id": "forest_004"},
                      {"id": "llanowar_elves_001"}, {"id": "grizzly_bears_002"}],
            "bob": [{"id": "mountain_001"}, {"id": "mountain_002"},
                    {"id": "goblin_raider_001"}],
        }
        self.window.refresh_ui()
        self.window.show()
        app.processEvents()

    def test_battlefield_hand_stack_and_actions_fit_demo_window(self):
        self._populate_board()
        self.window.resize(1510, 900)
        app.processEvents()
        central = self.window.centralWidget()
        for zone in (self.window.hand_list, self.window.your_battlefield_list,
                     self.window.opp_battlefield_list, self.window.stack_list,
                     self.window.exile_list):
            self.assertTrue(zone.isVisible(), zone.title.text())
            self.assertLessEqual(zone.mapTo(central, zone.rect().bottomRight()).y(),
                                 central.height(), zone.title.text())
        self.assertTrue(self.window.pass_btn.isVisible())
        self.assertTrue(self.window.concede_btn.isVisible())
        self.assertTrue(self.window.side_cast_btn.isVisible())
        self.assertEqual(self.window.side_cast_btn.text(), "CAST SPELL")
        self.assertEqual(self.window.phase_items["PRECOMBAT_MAIN"].text(), "> Main (1)")
        self.assertEqual(self.window.hand_list.count(), 6)
        self.assertEqual(self.window.your_battlefield_list.count(), 4)
        self.assertTrue(all(card.width() == 100 for card in
                            self.window.hand_list.findChildren(CardWidget)))
        screenshot_path = os.environ.get("MTGNP_UI_SCREENSHOT")
        if screenshot_path:
            self.assertTrue(self.window.grab().save(screenshot_path))

    def test_at_minimum_size_card_rows_stay_inside_window(self):
        self._populate_board()
        self.window.resize(1120, 730)
        app.processEvents()
        self.assertEqual(self.window.width(), 1120)
        self.assertEqual(self.window.height(), 730)
        for zone in (self.window.hand_list, self.window.your_battlefield_list,
                     self.window.opp_battlefield_list):
            self.assertLessEqual(zone.geometry().bottom(),
                                 zone.parentWidget().height(), zone.title.text())
        scrollbar = self.window.playmat_scroll.verticalScrollBar()
        self.assertGreater(scrollbar.maximum(), 0)
        scrollbar.setValue(scrollbar.maximum())
        app.processEvents()
        viewport = self.window.playmat_scroll.viewport()
        hand_bottom = self.window.hand_list.mapTo(
            viewport, self.window.hand_list.rect().bottomRight()
        ).y()
        self.assertLessEqual(hand_bottom, viewport.height())
        self.assertGreater(hand_bottom, 0)
        screenshot_path = os.environ.get("MTGNP_UI_SCREENSHOT_SMALL")
        if screenshot_path:
            self.assertTrue(self.window.grab().save(screenshot_path))

    def test_visible_mulligan_card_click_survives_refresh_and_keeps_physical_id(self):
        self.state.phase = "MULLIGAN"
        self.state.mulligan_seq_num = 50
        self.state.local_hand = ["forest_001", "forest_002"]
        self.window.refresh_ui()
        self.window.show()
        app.processEvents()

        self.window.mull_btn.click()
        self.window.dispatcher.send_mulligan_choice.assert_called_once_with(
            False, cards_to_bottom=[]
        )
        self.window.dispatcher.send_mulligan_choice.reset_mock()

        self.state.local_hand = ["forest_003", "forest_004"]
        self.window.refresh_ui()
        app.processEvents()
        self.assertIn("exactly 1", self.window.mulligan_status.text())

        card = next(widget for widget in self.window.mulligan_cards.findChildren(CardWidget)
                    if widget.card.card_id == "forest_004")
        QTest.mouseClick(card, Qt.LeftButton)
        self.assertEqual(self.window.mulligan_cards.selected_card_ids(), ["forest_004"])
        self.assertEqual(self.window._mulligan_cards_selected(), ["forest_004"])

        self.state.last_pong_timestamp = 123
        self.window.refresh_ui()
        app.processEvents()
        self.assertEqual(self.window.mulligan_cards.selected_card_ids(), ["forest_004"])

        self.window.keep_btn.click()
        self.window.dispatcher.send_mulligan_choice.assert_called_once_with(
            True, cards_to_bottom=["forest_004"]
        )
        self.assertEqual(self.window.mulligan_status.text(),
                         "Hand kept. Waiting for opponent...")
        self.assertFalse(self.window.keep_btn.isEnabled())
