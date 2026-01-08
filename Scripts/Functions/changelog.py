from datetime import datetime
import json



def update_changelog(message):
    changelog = json.load(open(f"Changelog.json", encoding="utf8"))
    time = datetime.today().strftime('%Y.%m.%d.%H.%M.%S')
    changelog[time] = message

    with open(f'Chanelog.json', 'w+') as outfile_kaz:
        json.dump(changelog, outfile_kaz, indent=4)