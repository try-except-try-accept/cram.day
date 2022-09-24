
from flask import Markup
from database import get_chart_data
from random import randint


def get_hex_shades(n):
	colours = []
	r, g, b = randint(1, 255), randint(1, 255), randint(1, 255)

	rc, gc, bc = randint(0, 1), randint(0, 1), randint(0, 1)

	change = randint(1, 25)

	for i in range(n):

		colours.append("#" + hex(r)[2:].zfill(2) + hex(g)[2:].zfill(2) + hex(b)[2:].zfill(2))

		if rc and 255-change > r:
			r += change
		if gc and 255-change > g:
			g += change
		if bc and 255-change > b:
			b += change

	return colours

def get_chart():
	chart_data = get_chart_data()

	title = chart_data["title"]

	answers, counts = [], []




	for row in chart_data["data"]:
		if "Most Popular" in title:
			answers.append(row[0])
			counts.append(row[1])
		elif "Letter" in title:
			answers.append(row[0])
			counts.append(round(row[1] / row[2], 2))
		elif "Top 25" in title:
			answers.append(row[1])
			counts.append(row[3])
	try:
		answers = '"' + '","'.join(str(a) for a in answers) + '"'
		counts = ",".join(str(i) for i in counts)

		colours = '"' + '","'.join(get_hex_shades(len(counts))) + '"'

		chart = f'''<script>
			new	Chart("stats_display", {{
			type: "bar",
			data: {{
				labels: [{answers}],
				datasets: [{{
					backgroundColor: [{colours}],
					data: [{counts}]
				}}]
			}},
			  options: {{
				legend: {{display: false}},
				title: {{
				  display: true,
				  text: "{title}"
				}}
			  }}
		}});
		
		</script>'''

		return Markup(chart)
	except Exception as e:
		print(e)
		return "<problem rendering stats>"