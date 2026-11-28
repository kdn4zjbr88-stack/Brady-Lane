# Brady

A cheeky adults-only life sim set in the town of **Genitopia**. Pick your character (a penis or a vagina), choose skin and hair colour, then walk around town keeping them healthy, clean, happy and safe for 30 days. Every resident of Genitopia is a soft-shaded cartoon mascot.

## Run

**Play online:** https://kdn4zjbr88-stack.github.io/Brady-Lane/ (GitHub Pages, served from `docs/`).

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
| B | Family menu: feed/cuddle the baby, feed/play with pets |
| SPACE | Swing the bat (at the stadium) |
| Esc | Close phone or pop-up |
| F11 | Fullscreen (desktop version; the browser version fills the window automatically) |

Walk up to a door, furniture, a resident or an event and choices pop up.

## Genitopia

| Place | What you can do |
| --- | --- |
| Home | Sleep, shower, toilet, fridge, mirror, crib, plus any upgrades you buy |
| Bean's Diner | Meals and pregnancy cravings (Chef Bean). Job: line cook |
| Office | Job: office assistant (Boss Richard) |
| Pharmacy | Condoms, tests, morning-after pill, formula, pads & tampons, painkillers (Patty). Job: clerk |
| Genitopia General | STI tests, prenatal checkups, delivering the baby (Dr. Ova) |
| Ink & Steel | Piercings (Pierce). Job: apprentice |
| Club Velvet | Evening only, no babies: drinks with Rocco, dancing, chatting people up. Job: bartender |
| Ballers Stadium | Watch games, batting practice, play in games (Coach Rod). Job: concessions |
| Screw & Nail | Home upgrades (Mandy) |
| Apartments | Your date's bedroom, unlocked when someone is expecting you |
| Rock Solid Jewelers | Engagement rings and necklaces (Goldie) |
| Petal Pushers | Roses, chocolates, teddy bears to give as gifts (Fern) |
| Nuts & Eggs | Pets: a pair of testicles, a set of ovaries or a pet sperm, plus pet food (Tad) |
| Birthday Suits | Sunglasses, cowboy hat, flower crown, bow tie, gold chain: worn on your character, +charm (Vee) |
| Genitopia Chapel | Weddings (Reverend Love) |
| Pump House Gym | Workouts for fitness (Brick). Job: personal trainer |

Around town you'll meet **Mayor Johnson**, **Granny Muffin** on her bench, **Officer Woody** on patrol and **Jaz** jogging around the fountain.

**Dialogue changes every day:** each resident has a daily rotation of lines, topical things to say (rain, game days, last night's score, your overdue bills, your period, your hot tub, the weekday, your baby...) and fresh town gossip.

**Town events** pop up at random: a street musician, a taco truck, a lost wallet, a free condom stand, a block party, a stray puppy, a piercing flash sale, a street preacher, and rain.

## Romance with the residents

Talking raises affection. Then you can **Flirt** (a charm check, once a day), **Ask on a date** (from 35 affection, $25) and, from 65 affection, ask them to **come over tonight**: they'll be waiting in your bedroom. Granny Muffin, Dr. Ova and Boss Richard will politely turn you down.

## Going steady, engagement and marriage

Right after hooking up with anyone (a resident, a Spark match or someone from the club) you can ask them to be your **boyfriend/girlfriend**; chemistry and charm decide the answer. You can also ask a resident while chatting once they're at 65+ affection. Partners text you, miss you if you ignore them for 3 days, love gifts (double affection) and will dump you if they catch you cheating. Buy a ring at Rock Solid, wait at least 3 days together, reach 85+ affection and **propose**. Then get married at Genitopia Chapel: your spouse moves in (home in the evenings), chips in money every day, helps with the baby and halves your rent. Partners you met on Spark or at the club can be proposed to in the bedroom.

## Pets

Adopt up to two pets at Nuts & Eggs and name them. They follow you around, need feeding and playtime (B), and keep your mood up when they're happy.

## Jobs and bills

Six jobs, each with its own hours, pay and perk; apply at the workplace (some need enough charm). Every 6 shifts you get a raise. Rent, power & water, and your phone plan are due every 7 days; pay them in the phone's Bills app. Late bills cost a fee, unpaid utilities shut off your shower and kitchen, an unpaid phone kills the dating app, and rent 4 days late gets you evicted.

## Baseball

The Genitopia Ballers play every 3rd day in the evening. Watch from the bleachers, take batting practice in the cage, or step up to home plate and play: press SPACE to swing as the pitch arrives (fastball, changeup, curveball). Wins pay a bonus and make you famous, which adds charm.

## House upgrades

Luxury bed, rain shower, chef's kitchen, giant TV, home gym, hot tub and a dreamy nursery, each shown in your home with something new to do. Upgrades raise your power bill a little.

## Menstrual cycle

Playing the vagina character, you have a (compressed, 10-day) cycle tracked in the phone's Cycle app: a period that needs supplies and can bring cramps, a fertile window where unprotected sex is much riskier, and PMS. Pregnancy pauses it.

## Ending a pregnancy

If you're pregnant (and know it), Dr. Ova at Genitopia General can talk you through ending the pregnancy: medication up to day 7 or an in-clinic procedure up to day 10, with a day or two of rest afterwards. If you play the penis character, the decision is your partner's.

## Dating

Open the phone and swipe right or left. Matches depend on your charm (hygiene, mood, piercings). Text a match in the evening to get invited over to the Apartments.

## Risk, pregnancy and babies

Each encounter is a choice: condom, or no condom and then pull out or finish inside. Partners carry a hidden STI risk, and each choice has a hidden pregnancy risk.

A pregnancy shows after a few days: morning sickness, back aches, tiredness and cravings, and a vagina character's belly grows over time. If you play the penis, your partner texts you the updates and cravings instead. Around day 12 labor starts: get to Genitopia General within a day, or the baby arrives without you.

The baby is yours to customise (name, skin, hair, onesie, bow/beanie/pacifier). They follow you around town, need feeding (formula from the Pharmacy) and cuddles, and can be left in the crib at home when you go out.

If you play the penis and get someone pregnant, the baby comes home with you: you raise them too. Neglect the baby (a whole day without food) and Family Services gives you one warning; the second time the baby goes to live with the other parent and you pay weekly child support.

## Tests

```bash
python -m pytest
```

## Play in a browser

To rebuild the single-file version after changing the game: `pip install pygbag`, then `python tools/make_single_html.py`.

Or serve the build folder:

```bash
pip install pygbag
python -m pygbag --build .
python tools/serve_web.py 8000
```

Then open http://localhost:8000 and click once to start. The page downloads its Python runtime from pygame-web.github.io, so the first load takes a few seconds.
