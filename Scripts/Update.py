import json
import requests
import os
import time
from Functions import discord

print("open old Lists")
brw = json.load(open(f"Brandweer.json", encoding="utf8"))
amb = json.load(open(f"Ambulance.json", encoding="utf8"))
kaz = json.load(open(f"Kazernes.json", encoding="utf8"))

print("Get new lists")
brw_new = requests.get(os.getenv("BRW_URL")).json()
amb_new = requests.get(os.getenv("AMB_URL")).json()
kaz_new = requests.get(os.getenv("KAZ_URL")).json()

print("Check brandweer")
for x in brw_new:
    if next((False for y in brw if y["Roepnummer"] == x["Roepnummer"]), True):
        discord.webhook(f'{x["Roepnummer"]} has been added ```{x}```')
        time.sleep(10)
        continue
    old = [z for z in brw if z["Roepnummer"]==x["Roepnummer"]]
    if not old[0] == x:
        discord.webhook(f"Entry Changed:\n ```{old[0]}```\nHas been changed to: ```{x}```")
        time.sleep(10)
        continue

for x in brw:
    if next((False for y in brw_new if y["Roepnummer"] == x["Roepnummer"]), True):
        discord.webhook(f'{x["Roepnummer"]} has been removed ```{x}```')
        time.sleep(10)
        continue

print("Check ambulance")
for x in amb_new:
    if next((False for y in amb if y["Roepnummer"] == x["Roepnummer"]), True):
        discord.webhook(f'{x["Roepnummer"]} has been added ```{x}```')
        time.sleep(10)
        continue
    old = [z for z in amb if z["Roepnummer"]==x["Roepnummer"]]
    if not old[0] == x:
        discord.webhook(f"Entry Changed:\n ```{old[0]}```\nHas been changed to: ```{x}```")
        time.sleep(10)
        continue

for x in amb:
    if next((False for y in amb_new if y["Roepnummer"] == x["Roepnummer"]), True):
        discord.webhook(f'{x["Roepnummer"]} has been removed ```{x}```')
        time.sleep(10)
        continue

print("Check kazerne")
for x in kaz_new:
    if next((False for y in kaz if y["Regio"] == x["Regio"] and y["Kazerne naam"] == x["Kazerne naam"]), True):
        discord.webhook(f'{x["Regio"]}-{x["Kazerne naam"]} has been added ```{x}```')
        time.sleep(10)
        continue
    old = [z for z in kaz if z["Regio"]==x["Regio"] and z["Kazerne naam"] == x["Kazerne naam"]]
    if not old[0] == x:
        discord.webhook(f"Entry Changed:\n ```{old[0]}```\nHas been changed to: ```{x}```")
        time.sleep(10)
        continue

for x in kaz:
    if next((False for y in kaz_new if y["Regio"] == x["Regio"] and y["Kazerne naam"] == x["Kazerne naam"]), True):
        discord.webhook(f'{x["Regio"]}-{x["Kazerne naam"]} has been removed ```{x}```')
        time.sleep(10)
        continue

print("save the new lists")

with open(f'Brandweer.json', 'w+') as outfile_brw:
    json.dump(brw_new, outfile_brw, indent=4)

with open(f'Ambulance.json', 'w+') as outfile_amb:
    json.dump(amb_new, outfile_amb, indent=4)

with open(f'Kazernes.json', 'w+') as outfile_kaz:
    json.dump(kaz_new, outfile_kaz, indent=4)
