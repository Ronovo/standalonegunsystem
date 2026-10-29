# Stand Alone Gun System (Text-Based)
Simple weapons system built in Python. The `gunsystem` library can be imported into other games; this repo also includes a range demo you can play in the browser (Flask) or in the terminal.

<p float="left">
  <img src="Resources/MainMenu.png" width="250" />
  <img src="Resources/Range Menu.png" width="250" /> 
  <img src="Resources/Shooting.png" width="250" />
</p>

## Set Up and Run
### 1.) Requires Python to be installed
  - Requires Python 3.10 or newer (the Docker image runs 3.12)
  - Get [Python](https://www.python.org/downloads/) here.
  - Run the Installer

### 2.) Download the project (Through Git or File Download)

### 3.) Navigate to the project with Powershell/Command Prompt
  - `cd (drive)/(File Location)/standalonegunsystem`

### 4.) Web version
  - Install the web extras once: `pip install -e ".[web]"` (Flask, PyJWT and ronovo-portfolio-auth)
  - Run `python -m webapp`
  - Open http://127.0.0.1:5000 in your browser
  - Menus can be clicked or driven from the keyboard: number keys pick an item, `Esc` goes back

### Web version in Docker
  - Build: `docker build -t gunsystem-web .`
  - Run: `docker run -d --name gunsystem-web -p 8000:8000 gunsystem-web`
  - Open http://127.0.0.1:8000
  - Set `-e GUNSYSTEM_SECRET_KEY=<random string>` to keep range sessions valid across container restarts
  - Balance text reports are written only when **Write text reports** is ticked, and inside the container; add `-v "${PWD}/Balance Reports:/app/Balance Reports"` to keep them on your machine
  - On every start the container runs `docker/git-sync.sh`, which fetches the latest commit on GitHub `main`
    over the code in the image, so a pushed commit goes live on the next restart. If GitHub can't be reached it
    starts on the code it already has. Set `-e REPO_URL=` to run exactly what is in the image instead
    (`REPO_BRANCH` picks another branch). When the fetched commit hasn't been built yet, `BUILD_CMD` reinstalls
    the packages listed in `pyproject.toml`, so they are pinned in one place

### Log in with a portfolio account
  - The range and destroyed count are kept in the browser for 31 days
  - With `PORTFOLIO_SSO_URL` (the portfolio's address) and `PORTFOLIO_SSO_PUBLIC_KEY` (printed by the portfolio's `python sso.py`) set, the top bar offers to log in with a portfolio account. It reads **Log in as** and the portfolio username when this browser is logged in to the portfolio
  - While logged in, that progress is also kept for the portfolio account in `DATA_DIR` (`data` in the folder you run from, `/app/data` in the container, so add a volume there). Logging in on another browser takes whichever range is newer and the higher destroyed count
  - When a different account logs in on the same browser, the progress kept there for the last account stays with that account instead of joining the new one. Range played after logging out belongs to nobody, and joins whichever account logs in next

### 5.) Terminal version
  - Run `python -m demo`
  - The game starts in your terminal window

## Using as a library
From the repo (or with `gunsystem/` on your Python path):

```python
from gunsystem import Catalog, Target, resolve_shot

gun = Catalog.create("M1911")
gun.reload()
result = resolve_shot(gun, Target(distance=100, size="m"))
```

`result` has `hit`, `damage`, `critical`, `remaining_ammo`, and `fired` (False when the weapon was empty).

`gunsystem.dummy` (practice dummies and their sizes) and `gunsystem.simulation` (magazine runs and the balance
reports) are the parts the terminal and web versions share.

## Tests
From the repo root, with the web extras installed:

```
python -m unittest discover -s tests -t .
```

The tests turn portfolio login on and off themselves and keep their data in temporary folders, so they don't
depend on the shell's settings or write into the repo.

## How a shot is resolved
1. A target past the gun's max range is always a miss.
2. Roll 1-100. Full auto and bursts multiply the roll as a string goes on (muzzle spray).
3. Distance changes it in 50 m bands: +10 for each band past the gun's range, and -5 for each band inside it
   (up to 3 bands, never below 0), so close shots hit more often. Snipers instead take +5 per band up close,
   up to 4 bands.
4. The dummy's size scales it (x1.1 small, x0.9 large); the shot hits when the result is at or below the gun's
   accuracy.
5. Damage drops by 25 for every 50 m past the gun's range, and a hit that does 0 damage counts as a miss.
6. A hit has a 1 in 200 chance to be critical: x3 damage 80% of the time, x2 the rest.

On full auto, bulk fire and balance reports fire in 10-round trigger pulls, the range's starting setting, and each
pull starts a new string just as it does on the range.

## V1.5 Features
- Hit Calculation
  - Dummy Size, Damage Drop off, "Bullet Drop", Muzzle Spray, Critical Chance
- Armory Menu to look at all your guns!
- Gun Range to test out all your guns!
  - Dynamic hit calculation based on Target Distance and Gun Type!
  - Counter to keep track of how many Dummies you have destroyed
- Bulk Fire report to test weapon balancing, with firing options per gun (up to 1000 shots)
- Balance Report Functionality
    - Writes one text file per weapon, dummy size and firing mode, in `Balance Reports/<Class>/<Weapon>/<Size>/<Mode>.txt` under the folder you run it from. The terminal always writes them; the browser only when **Write text reports** is ticked
    - In the browser, with portfolio login set up, running one needs a portfolio login, only one runs at a time, and each account sees its own latest results
    - Each Report includes stats for 15 Full Magazines shot at:
        - Each Type of Dummy
        - Every Range listed in the Range Menu
        - For Each Firing Mode (Single, 3 Round, Auto)
- 26 Guns, with 6 different weapon types! (See List Below!)

## Future Updates
- More Guns!!!!

## Gun List
### Pistols (Small Arms)
- M1911
- USP .45
- M9
- Desert Eagle
- Glock 18
- .38 Special
- 44 Magnum

### SMG (Small Arms)
- MP5
- AK-47u
- P90
- Mini-Uzi

### Shotguns (Medium Arms)
- W1200
- M1014
- USAS-12
- Spas-12

### ARs (Medium Arms)
- M16A4
- AK47
- G3
- G36
- FN FAL

### Snipers (Large Arms)
- M40A3
- Dragunov
- Barrett .50Cal

### LMGs (Large Arms)
- M249 SAW
- M60E4
- RPD
