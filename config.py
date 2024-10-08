DB_MODE = "lite"
ONE_HOUR = 3676  # 1h diff between datetime timestamps
ONE_DAY = 86400  # 24h diff between datetime timestamps
ONE_MIN = ONE_HOUR // 60
ADMIN_ID = '0'
WAIT_BEFORE_RESYNC = 60

# consider gap limit in future


LIGHT_MODE_COLOURS = '''#F2FFFF
#FFF2FF
#FFFFF2
#F2F2FF
#FFF2F2
#F2FFF2
#EEFFEE
#FFEEFF
#EEFFFF
#FFFFEE
#EFEFEF'''.splitlines()

DARK_MODE_COLOURS = '''#500000
#005000
#000050
#505000
#005050
#500050
#A0A000
#A000A0
#00A000
#0000A0'''.splitlines()



GAP_HTML = '''<input autocomplete="off" class="gap_textfield"
type="text"
style="background-color:{colour}"
ondrop="drop(event)" ondragover="allow_drop(event)"
id="answer{i}"
name="answer{i}" required>'''

LEADERBOARD_MODES = '''success rate
number of correct answers
biggest improvement'''.splitlines()

DISPLAY_MODES = '''light mode
dark mode
cream mode'''.splitlines()
