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
