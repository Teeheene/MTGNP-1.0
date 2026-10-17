"""Stitch-inspired dark fantasy palette shared by the production Qt pages."""

STITCH_THEME = """
QMainWindow, QWidget#AppRoot, QStackedWidget { background:#0c1116; color:#edf0eb; }
QWidget { color:#edf0eb; font-family:'Segoe UI'; font-size:12px; }
QLabel { background:transparent; }
QLabel#Brand { color:#f3eee5; font-family:Georgia; font-size:27px; font-weight:700; }
QLabel#BrandAccent { color:#ed873b; font-weight:700; font-size:11px; }
QLabel#Eyebrow { color:#dfa65b; font-size:11px; font-weight:700; }
QLabel#PageTitle { color:#f5f0e7; font-size:22px; font-weight:700; }
QLabel#Caption { color:#a9b1ad; font-size:12px; }
QLabel#Status { color:#f2ae5e; font-size:13px; font-weight:700; }
QLabel#Life { color:#a5dda5; font-weight:700; }
QLabel#ZoneTitle { color:#e0c697; font-size:11px; font-weight:700; }
QLabel#PlayerName { color:#f3f1eb; font-size:14px; font-weight:700; }
QLabel#Health { color:#ff8278; font-weight:700; font-size:13px; }
QLabel#PhaseCurrent { color:#a5f08a; font-weight:700; font-size:12px; }
QLabel#PhaseIdle { color:#8e9898; font-size:11px; }
QLabel#SectionTitle { color:#f3f0e8; font-size:14px; font-weight:700; }
QLabel#Instruction { color:#eac28d; font-size:12px; }
QLabel#Notice { color:#ecaa58; font-weight:700; }
QLabel#AvatarGreen { background:#173f28; color:#a9ef9c; border:2px solid #5e9f68; border-radius:22px; font-weight:700; }
QLabel#AvatarRed { background:#482920; color:#f7ae84; border:2px solid #a76742; border-radius:22px; font-weight:700; }
QFrame#Header { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #111b21,stop:1 #121519); border-bottom:1px solid #39413b; }
QFrame#Panel, QFrame#Sidebar, QGroupBox { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1a2226,stop:1 #11181d); border:1px solid #3d484a; border-radius:7px; }
QFrame#Playmat { background:qradialgradient(cx:0.47,cy:0.43,radius:0.94,fx:0.47,fy:0.43,stop:0 #34352e,stop:0.57 #252a27,stop:1 #161c1c); border:1px solid #625b47; border-radius:7px; }
QFrame#HeroArt { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0b161a,stop:0.36 #293126,stop:0.73 #3b2b1d,stop:1 #0d141b); border:1px solid #635643; border-radius:8px; }
QFrame#PlayerPlate { background:#13191c; border:1px solid #3b4845; border-radius:6px; }
QFrame#ZoneWidget { background:transparent; border:none; }
QFrame#HighlightBar { background:#1a2725; border:1px solid #406049; border-radius:6px; }
QFrame#PhaseRail { background:#141b1d; border:1px solid #4b5145; border-radius:6px; }
QFrame#ActionDock { background:#12191d; border:1px solid #445048; border-radius:7px; }
QScrollArea#CardScroll { background:rgba(8,14,14,0.28); border:1px solid #3c443c; border-radius:4px; }
QScrollArea#CardScroll QWidget { background:transparent; }
QScrollBar:horizontal { background:#111b1b; height:9px; border-radius:4px; }
QScrollBar::handle:horizontal { background:#6c795f; min-width:30px; border-radius:4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0px; }
QScrollBar:vertical { background:#12191a; width:10px; }
QScrollBar::handle:vertical { background:#53645b; border-radius:4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
QPushButton { background:#2a3335; color:#f5f3ec; border:1px solid #53605b; border-radius:5px; padding:8px 12px; font-weight:600; }
QPushButton:hover { background:#3a4b49; border-color:#819281; }
QPushButton:pressed { background:#4f5f55; }
QPushButton:disabled { background:#1a2023; color:#6b7575; border-color:#333b3d; }
QPushButton#Primary { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #bf702f,stop:1 #98411b); border:1px solid #dc8a45; color:white; font-weight:700; }
QPushButton#Primary:hover { background:#d17737; }
QPushButton#Keep { background:#205b28; border-color:#3a853f; color:#edffeb; font-weight:700; }
QPushButton#Keep:hover { background:#33773b; }
QPushButton#Danger { background:#662322; border-color:#9a4238; color:#fff0e9; font-weight:700; }
QPushButton#Danger:hover { background:#863630; }
QPushButton#Primary:disabled, QPushButton#Keep:disabled, QPushButton#Danger:disabled { background:#1a2023; color:#6b7575; border-color:#333b3d; }
QGroupBox { margin-top:11px; padding:13px; font-weight:700; }
QGroupBox::title { subcontrol-origin:margin; left:15px; color:#ebc08a; }
QListWidget, QTextEdit, QLineEdit, QComboBox { background:#121b21; border:1px solid #43504f; border-radius:4px; padding:7px; selection-background-color:#355e41; selection-color:#f4f7f1; }
QLineEdit:focus, QComboBox:focus, QListWidget:focus { border-color:#c68551; }
QComboBox::drop-down { border:0; width:20px; }
QDialog { background:#121a1e; color:#f0ede6; }
QToolTip { background:#25342e; color:#f2efe8; border:1px solid #82916b; padding:5px; }
"""

# Aetheric Grimoire / Google Stitch visual layer. Keep the shared rules above
# for non-board controls while replacing the former teal/orange game palette.
STITCH_THEME += """
QMainWindow, QWidget#AppRoot, QStackedWidget { background:#16130b; color:#eae1d4; }
QWidget { color:#eae1d4; }
QLabel#Brand { color:#f2ca50; font-family:Georgia; font-size:29px; }
QLabel#BrandAccent { color:#b7a782; font-size:10px; }
QLabel#HeaderActive { color:#f2ca50; background:#292418; border-bottom:3px solid #f2ca50; padding:13px 14px; font-family:Georgia; font-size:17px; font-weight:700; }
QLabel#Eyebrow { color:#d4af37; }
QLabel#PageTitle { color:#f5e8c8; font-family:Georgia; }
QLabel#Caption { color:#b9ac96; }
QLabel#Status { color:#f2ca50; }
QLabel#Life { color:#e9d9ad; }
QLabel#ZoneTitle { color:#dfc784; }
QLabel#PlayerName { color:#f0dfb5; font-family:Georgia; }
QLabel#Health { color:#f3b6a7; font-size:16px; }
QLabel#PhaseCurrent { color:#f2ca50; }
QLabel#PhaseIdle { color:#ac9f86; }
QLabel#SectionTitle { color:#ecd9ac; font-family:Georgia; font-size:16px; }
QLabel#Instruction { color:#e4cb8c; }
QLabel#Notice { color:#f2b784; }
QLabel#AvatarGreen { background:#222717; color:#d8de9a; border-color:#ab9141; border-radius:20px; }
QLabel#AvatarRed { background:#36251e; color:#f3be98; border-color:#a67c4b; border-radius:20px; }
QLabel#ArchmagePortrait { color:#f5d775; font-family:Georgia; font-size:50px; background:qradialgradient(cx:0.5,cy:0.4,radius:0.8,fx:0.5,fy:0.4,stop:0 #3e443e,stop:0.5 #282d2e,stop:1 #151712); border:2px solid #d4af37; border-radius:12px; }
QLabel#RailPlayerName { color:#f2ca50; font-family:Georgia; font-size:17px; font-weight:700; }
QLabel#RailRank { color:#a99d83; font-size:10px; font-weight:700; }
QFrame#Header { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #262218,stop:1 #1c1a14); border-bottom:1px solid #4d4635; }
QFrame#Panel, QFrame#Sidebar, QGroupBox { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2b271e,stop:1 #1b1913); border:1px solid #433a2a; }
QFrame#Playmat { background:qradialgradient(cx:0.51,cy:0.44,radius:0.87,fx:0.51,fy:0.44,stop:0 #766744,stop:0.55 #50442e,stop:1 #2e281e); border:1px solid #6b5c3d; border-radius:5px; }
QFrame#HeroArt { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #15140e,stop:0.4 #33301e,stop:0.74 #4f3d21,stop:1 #19160f); border-color:#6d5935; }
QFrame#PlayerPlate { background:rgba(20,18,13,0.72); border:1px solid #4b402d; }
QFrame#BattlefieldDivider { background:rgba(16,15,10,0.40); border:0px; border-top:1px solid #8b743b; border-bottom:1px solid #8b743b; }
QFrame#ArcaneRail { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e1b12,stop:1 #130f0a); border:0px; border-right:1px solid #514630; }
QFrame#ActionDock { background:#1b1812; border-color:#463d2d; }
QScrollArea#BattlefieldScroll { background:transparent; border:0px; }
QScrollArea#CardScroll { background:rgba(19,16,11,0.12); border:1px solid rgba(190,164,101,0.26); }
QScrollBar:horizontal, QScrollBar:vertical { background:#17150f; }
QScrollBar::handle:horizontal, QScrollBar::handle:vertical { background:#817048; }
QPushButton { background:#332d22; color:#eae1d4; border-color:#695d43; }
QPushButton:hover { background:#4c412c; border-color:#bb9e54; }
QPushButton:pressed { background:#655231; }
QPushButton:disabled { background:#211f1a; color:#817867; border-color:#39352b; }
QPushButton#Primary { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffe076,stop:1 #d4af37); border-color:#f2ca50; color:#352b0a; font-family:Georgia; font-size:14px; font-weight:700; }
QPushButton#Primary:hover { background:#ffe691; border-color:#fff0b0; }
QPushButton#Keep { background:#33452b; border-color:#7d9861; color:#f1f8df; }
QPushButton#Keep:hover { background:#49613b; }
QPushButton#Danger { background:#532b25; border-color:#97554a; color:#fae1d9; }
QPushButton#Danger:hover { background:#743831; }
QPushButton#Primary:disabled, QPushButton#Keep:disabled, QPushButton#Danger:disabled { background:#211f1a; color:#817867; border-color:#39352b; }
QGroupBox::title { color:#eccb78; }
QListWidget, QTextEdit, QLineEdit, QComboBox { background:#17150f; border-color:#5a5038; selection-background-color:#806c37; selection-color:#ffebbf; }
QLineEdit:focus, QComboBox:focus, QListWidget:focus { border-color:#f2ca50; }
QDialog { background:#211d15; color:#eae1d4; }
QToolTip { background:#3b3426; color:#f5e6bb; border-color:#b49750; }
"""
