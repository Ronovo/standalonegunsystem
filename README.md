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
  - Balance text reports are saved inside the container; add `-v "${PWD}/Balance Reports:/app/Balance Reports"` to keep them on your machine
  - On every start the container runs `docker/git-sync.sh`, which fetches the latest commit on GitHub `main`
    over the code in the image, so a pushed commit goes live on the next restart. If GitHub can't be reached it
    starts on the code it already has. Set `-e REPO_URL=` to run exactly what is in the image instead
    (`REPO_BRANCH` picks another branch). Python packages are installed when the image is built, so a change to
    them needs a rebuild

### Log in with a portfolio account
  - The range and destroyed count are kept in the browser for 31 days
  - With `PORTFOLIO_SSO_URL` (the portfolio's address) and `PORTFOLIO_SSO_PUBLIC_KEY` (printed by the portfolio's `python sso.py`) set, the top bar offers to log in with a portfolio account. It reads **Log in as** and the portfolio username when this browser is logged in to the portfolio
  - While logged in, that progress is also kept for the portfolio account in `DATA_DIR` (`/app/data` in the container, so add a volume there). Logging in on another browser takes whichever range is newer and the higher destroyed count
  - When a different account logs in on the same browser, the progress kept there for the last account stays with that account instead of joining the new one

### 5.) Terminal version
  - Run `python ./main.py` (or `python -m demo`)
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

## Tests
From the repo root, with the web extras installed:

```
python -m unittest discover -s tests -t .
```

## How a shot is resolved
1. Roll 1-100. Full auto and bursts multiply the roll as a string goes on (muzzle spray).
2. Distance changes it in 50 m bands past the gun's range, and snipers take a penalty up close.
3. The dummy's size scales it; the shot hits when the result is at or below the gun's accuracy.
4. Damage drops by 25 for every 50 m past the gun's range, and a hit that does 0 damage counts as a miss.
5. A hit has a 1 in 200 chance to be critical: x3 damage 80% of the time, x2 the rest.

Bulk fire and balance reports treat a whole magazine as one string on full auto, so they spray more than the
range does, where each trigger pull starts a new string.

## V1.5 Features
- Hit Calculation
  - Dummy Size, Damage Drop off, "Bullet Drop", Muzzle Spray, Critical Chance
- Armory Menu to look at all your guns!
- Gun Range to test out all your guns!
  - Bulk Fire report to test weapon balancing
  - Dynamic hit calculation based on Target Distance and Gun Type!
  - Counter to keep track of how many Dummies you have destroyed in the session!
  - Bulk Firing Options Per Gun
- Balance Report Functionality
    - Creates one report per weapon, dummy size and firing mode, in `Balance Reports/<Class>/<Weapon>/<Size>/<Mode>.txt` under the folder you run it from
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
