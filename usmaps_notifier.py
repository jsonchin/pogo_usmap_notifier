import requests
import datetime
import fbchat

usmap_sj_base_url = 'https://usmaps.me/raw_data?by=san-jose&excluded=7%2C10%2C13%2C14%2C16%2C17%2C19%2C21%2C23%2C25%2C27%2C29%2C32%2C37%2C39%2C41%2C43%2C46%2C48%2C50%2C52%2C54%2C56%2C58%2C60%2C63%2C69%2C72%2C74%2C77%2C79%2C81%2C84%2C86%2C90%2C92%2C96%2C98%2C100%2C116%2C118%2C120%2C122%2C124%2C129%2C133%2C158%2C161%2C162%2C163%2C165%2C166%2C167%2C170%2C177%2C183%2C185%2C187%2C190%2C191%2C194%2C198%2C200%2C209%2C215%2C216%2C218%2C220%2C221%2C223&pokemon=true&pokestops=false&gyms=false&scanned=false&spawnpoints=false&swLat=37.32526006760127&swLng=-122.17809677124025&neLat=37.457009304251244&neLng=-121.98154449462892&alwaysperfect=false&_={}'

google_maps_base_url = 'https://www.google.com/maps?q={},{}'

ms_time = int(datetime.datetime.now().timestamp()*1000)
usmap_sj_url = usmap_sj_base_url.format(ms_time)
pokemons = requests.get(usmap_sj_url).json()['pokemons']

# read in a list of pokemon that we have already encountered
seen_encounter_ids = {}
with open('encounter_ids.txt', 'r') as f:
    for line in f:
        encounter_id, disappear_time = line.strip().split()
        seen_encounter_ids[encounter_id] = int(disappear_time)

# define the pokemon that we will be notified on
POKEMON_NOTIFY = set(['Chansey',
                        'Blissey',
                        'Larvitar',
                        'Pupitar',
                        'Tyranitar',
                        'Snorlax',
                        'Dratini',
                        'Dragonair',
                        'Dragonite',
                        # 'Shuckle',
                        # 'Aerodactyl',
                        'Unown',
                        'Grimer',])

# add pokemon to the list if they are valid (within the box, not encountered yet, rarity, etc)
spotted_pokemon = []
for pokemon_d in pokemons:
    lon = pokemon_d['longitude']
    lat = pokemon_d['latitude']
    encounter_id = str(pokemon_d['encounter_id'])
    # pokemon_rarity = pokemon_d['pokemon_rarity']
    # if not (pokemon_rarity == 'Rare' or pokemon_rarity == 'Very Rare'):
    #     continue

    pokemon_name = pokemon_d['pokemon_name']
    if pokemon_name not in POKEMON_NOTIFY:
        continue

    if encounter_id in seen_encounter_ids:
        continue
    else:
        seen_encounter_ids[encounter_id] = pokemon_d['disappear_time']

    # define a box that is valid
    if lat > 37.353387 and lat < 37.413113 and lon < -122.048680 and lon > -122.095766:
        print(lat, lon)
        spotted_pokemon.append(pokemon_d)

# write the non-expired encounters to a file BEFORE fb messaging (fb messaging could take time)
with open('encounter_ids.txt', 'w') as f:
    for encounter_id in seen_encounter_ids:
        if seen_encounter_ids[encounter_id] >= ms_time:
            f.write('{} {}\n'.format(encounter_id, seen_encounter_ids[encounter_id]))

# make a connection to the fb client
fb_id = "EMAIL"
fb_pw = "PW"
group_chat_id = "GROUP CHAT ID (int)"
fb_client = fbchat.Client(fb_id, fb_pw)

# for each new valid encounter, message the group
for pokemon_d in spotted_pokemon:
    pokemon_name = pokemon_d['pokemon_name']

    disappear_time_ms = pokemon_d['disappear_time']
    disappear_datetime = datetime.datetime.fromtimestamp(disappear_time_ms//1000)
    disappear_time_formatted = disappear_datetime.strftime('%I:%M:%S%p')
    now_datetime = datetime.datetime.now()
    remaining_seconds = (disappear_datetime - now_datetime).seconds

    lon = pokemon_d['longitude']
    lat = pokemon_d['latitude']
    google_maps_url = google_maps_base_url.format(lat, lon)

    msg_text = '{} till {} ({}m {}s). {}'.format(pokemon_name,
                                    disappear_time_formatted,
                                    remaining_seconds // 60,
                                    remaining_seconds % 60,
                                    google_maps_url
                                )
    fb_client.send(group_chat_id, msg_text, is_user=False) #denote that it is a thread/group chat
