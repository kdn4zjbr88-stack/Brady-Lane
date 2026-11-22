# Brady

A cheeky adults-only life sim set in the town of **Genitopia**. Pick your character (a penis or a vagina), choose skin and hair colour, then walk around town keeping them healthy, clean, happy and safe for 30 days. Every resident of Genitopia is a soft-shaded cartoon mascot.

## Run

**Easiest (any computer):** double-click `Play Brady.html`. It opens in your web browser; no install needed, just an internet connection. Click once inside the game if it doesn't start.

**Mac, easiest:** double-click `Play Brady.command`. The first time, macOS may block it: right-click it, choose **Open**, then **Open** again.

**Any computer, from a terminal:**

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
| --- | --- |
| WASD / arrows | Walk |
| 1-5 or click | Pick a choice from the pop-up |
| E / Enter / Space | Pick the first available choice |
| P / Tab | Open the phone (Spark dating app) |
| B | Baby menu (feed, cuddle) |
| Esc | Close phone or pop-up |

Walk up to a door, furniture, a resident or an event and choices pop up.

## Genitopia

| Place | What you can do |
| --- | --- |
| Home | Sleep, shower, toilet, fridge, mirror, crib |
| Bean's Diner | Meals, and whatever a pregnancy craving demands (Chef Bean) |
| Office | Work shifts (Boss Richard) |
| Pharmacy | Condoms, pregnancy tests, morning-after pill, baby formula (Pharmacist Patty) |
| Genitopia General | STI tests, prenatal checkups, delivering the baby (Dr. Ova) |
| Ink & Steel | Piercings (Pierce) |
| Club Velvet | Evening only, no babies: drinks with Rocco, dancing, chatting people up |
| Apartments | Your date's bedroom, unlocked when someone is expecting you |

Around town you'll meet **Mayor Johnson**, **Granny Muffin** on her bench and **Officer Woody** on patrol. Everyone has things to say, and what they say changes with your situation (smelly, pregnant, new baby...).

**Town events** pop up at random: a street musician, a taco truck, a lost wallet, a free condom stand, a block party, a stray puppy, a piercing flash sale, a street preacher, and rain.

## Dating

Open the phone and swipe right or left. Matches depend on your charm (hygiene, mood, piercings). Text a match in the evening to get invited over to the Apartments.

## Risk, pregnancy and babies

Each encounter is a choice: condom, or no condom and then pull out or finish inside. Partners carry a hidden STI risk, and each choice has a hidden pregnancy risk.

A pregnancy shows after a few days: morning sickness, back aches, tiredness and cravings, and a vagina character's belly grows over time. If you play the penis, your partner texts you the updates and cravings instead. Around day 12 labor starts: get to Genitopia General within a day, or the baby arrives without you.

The baby is yours to customise (name, skin, hair, onesie, bow/beanie/pacifier). They follow you around town, need feeding (formula from the Pharmacy) and cuddles, and can be left in the crib at home when you go out.

## Tests

```bash
python -m pytest
```

## Play in a browser

To rebuild the single-file version after changing the game: `python -m pygbag --build .` then `python tools/make_single_html.py`.

Or serve the build folder:

```bash
pip install pygbag
python -m pygbag --build .
python tools/serve_web.py 8000
```

Then open http://localhost:8000 and click once to start. The page downloads its Python runtime from pygame-web.github.io, so the first load takes a few seconds.
