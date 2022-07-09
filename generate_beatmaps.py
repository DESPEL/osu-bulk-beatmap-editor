# You Can Modify These Values
OSU_FOLDER = "D:\\osu! ranked"
NEW_OSU_FOLDER = "D:\\osu! training"

MUSIC_ONLY = True # False transfers all the beatmap folder contents

BEATMAP_OD = ["7","10"]
BEATMAP_SV = [ # Multiplier of original
    "0.5", "0.6", "0.7", "0.8", "0.9",
    "1.0", "1.1", "1.2", 
    # "1.3", "1.4", "1.5"
]
MIN_STARS = 6.5
MAX_STARS = 8 

NUMBER_OF_THREADS = 24 # Multiprocessing, may use 100% CPU | 100% Disk
# END OF Modifiable Values 


FOLDERS_TO_TRANSFER = [
    "Localisation",
    "Skins",
]

import osutools
import json
import os
from multiprocessing import Pool
from math import ceil
from time import sleep
import shutil

# Load beatmap info from osu.db
def load_data():
    if not os.path.exists("./maps.json"):    
        osu = osutools.osuclient.OsuClientV1("token") # No token required
        osu.set_osu_folder(OSU_FOLDER)
        beatmap_data = { beatmap.beatmap_id: {
            "taiko_sr_ratings": beatmap.taiko_sr_ratings,
            "audio_filename": beatmap.audio_filename,
        } for beatmap in osu.osu_db.map_list()}
        with open("maps.json", 'w+') as f:
            json.dump(beatmap_data, f)

    with open("maps.json", "r") as f:
        return json.load(f)

# Load raw beatmaps from .osu file
def get_beatmap_metadata(file):
    metadata = {}
    with open(file, "r", encoding="utf8") as f:
        category = None
        file_data = list(f.readlines())
        for line in file_data:
            line = line.strip()
            # Metadata Category
            if not line:
                continue
            if line[0] == '[' and line[-1] == ']':
                category = line[1:-1]
                metadata[category] = {}
                # The beatmap data starts after the [Events] category
                if (category.lower() == "events"):
                    break 
                continue
            if ":" in line:
                # Format: key:value
                key = line.split(':')[0].strip()
                value = ':'.join(line.split(':')[1:]).strip()
                metadata[category][key] = value
    metadata["RAW_FILE"] = file_data
    return metadata
 
# Returns "RAW_FILE" value updated
def update_beatmap_metadata(metadata):
    new_file = [x for x in metadata['RAW_FILE']]
    category = None
    for i, line in enumerate(metadata["RAW_FILE"]):
        line = line.strip()
        # Metadata Category
        if not line:
            continue
        if line[0] == '[' and line[-1] == ']':
            category = line[1:-1]
            # The beatmap data starts after the [Events] category
            if (category.lower() == "events"):
                break 
            continue
        if ":" in line:
            if category not in metadata: 
                continue
            key = line.split(':')[0]
            if key not in metadata[category]:
                continue
            value = metadata[category][key]
            new_file[i] = f"{key}:{value}\n"
    return new_file


def get_beatmaps():
    beatmaps_folder = OSU_FOLDER + "\\Songs"
    mapsets = {}
    for (root, dirs, files) in os.walk(beatmaps_folder):
        for file in files:
            if ".osu" not in file:
                continue
            if root not in mapsets:
                mapsets[root] = []
            mapsets[root].append((root, file))
    return mapsets



def generate_beatmaps(arg):
    beatmap_data, beatmaps, thread_no = arg

    total = len(beatmaps)
    for i, (mapset, diffs) in enumerate(beatmaps):
        if i % 100 == 0:
            print(f"Thread {thread_no}: Completed {i}/{len(beatmaps)}")
        for (path, diff_file) in diffs:
            new_path = path.replace(OSU_FOLDER, NEW_OSU_FOLDER)
            metadata = get_beatmap_metadata(f"{path}\\{diff_file}")
            # Only process taiko maps
            if "Metadata" not in metadata:
                continue
            if "BeatmapID" not in metadata["Metadata"]:
                continue
            if "Mode" not in metadata["General"]:
                continue
            if int(metadata["General"]["Mode"]) != 1:
                continue
            
            if not metadata["Metadata"]["BeatmapID"] in beatmap_data:
                continue
            map_stars = beatmap_data[metadata["Metadata"]["BeatmapID"]]["taiko_sr_ratings"][0][1]
            if MIN_STARS > map_stars or map_stars > MAX_STARS:
                continue

            # New File Format: Artist - Title (Creator) [Difficulty].osu
            new_diff_info = [(od, sv) for od in BEATMAP_OD for sv in BEATMAP_SV]
            diff_name = metadata["Metadata"]["Version"]
            orig_sv = metadata["Difficulty"]["SliderMultiplier"]
            for od,sv in new_diff_info:
                metadata["Metadata"]["Version"] = f"{diff_name} [OD{od}-SV{sv}]"
                metadata["Difficulty"]["OverallDifficulty"] = od
                metadata["Difficulty"]["SliderMultiplier"] = float(sv) * float(orig_sv)

                filename = f"{metadata['Metadata']['Artist']} - {metadata['Metadata']['Title']} ({metadata['Metadata']['Creator']}) [{metadata['Metadata']['Version']}].osu"
                invalid = '<>:"/\|?*'
                for char in invalid:
                    filename = filename.replace(char, '')
                
                try:
                    os.makedirs(new_path, exist_ok=True)
                    with open(f'{new_path}\\{filename}', "w+", encoding="utf8") as f:
                        map_data = update_beatmap_metadata(metadata)
                        f.writelines(map_data)
                    
                    if not os.path.exists(f'{new_path}\\{metadata["General"]["AudioFilename"]}'):
                        shutil.copyfile(
                            f'{path}\\{metadata["General"]["AudioFilename"]}', 
                            f'{new_path}\\{metadata["General"]["AudioFilename"]}'
                        )
                except:
                    print(f"Error saving beatmap: {diff_name} [OD{od}-SV{sv}]")
    print(f"Thread {thread_no}: Finished!")


if __name__ == "__main__":
    if not os.path.exists(NEW_OSU_FOLDER):
        print("Step 0: Creating new Osu Folder")
        for file in os.listdir(OSU_FOLDER):
            if ".db" in file:
                continue
            if os.path.isfile(f"{OSU_FOLDER}\{file}"):
                shutil.copy(f"{OSU_FOLDER}\{file}", f"{NEW_OSU_FOLDER}\{file}")

    print("Step 1: Getting List of Beatmaps")
    # Object format (Mapset Path, [List of maps (path, file)])
    beatmaps = list(get_beatmaps().items())
    beatmaps_per_thread = ceil(len(beatmaps) / NUMBER_OF_THREADS)

    print("Step 2: Loading osu!.db")
    beatmap_data = load_data()
    
    print("Step 3: Creating threads")
    thread_data = []
    for i, start in enumerate(range(0, len(beatmaps), beatmaps_per_thread)):
        thread_data.append((
            beatmap_data, beatmaps[start:start+beatmaps_per_thread], i+1
        ))

    with Pool(NUMBER_OF_THREADS) as p:
        p.map(generate_beatmaps, thread_data)
    print(len(beatmaps))















