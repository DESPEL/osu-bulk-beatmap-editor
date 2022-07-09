# You Can Modify These Values
OSU_FOLDER = "D:\\osu! ranked"
NEW_OSU_FOLDER = "D:\\osu! training"

MUSIC_ONLY = True # False transfers all the beatmap folder contents

BEATMAP_OD = ["10"]
BEATMAP_SV = [ # Multiplier of original
    "0.6", "0.7", "0.8", "0.9",
    "1", "1.1", "1.2", "1.3"
]
MIN_STARS = 6.5
MAX_STARS = 8 

NUMBER_OF_THREADS = 1 # Multiprocessing, may use 100% CPU | 100% Disk
# END OF Modifiable Values 


FOLDERS_TO_TRANSFER = [
    "Localisation",
    "Skins",
]
FOLDERS_TO_CREATE = [
    "Downloads",
    "Exports",
    "Logs",
    "Replays",
    "Screenshots",
    "Songs",
]
ROOT_FILES = [
    ".cfg",
    "osu!.exe",
    "repair osu!",
]

import osutools

# Load beatmap info from osu.db
def load_data():
    osu = osutools.osuclient.OsuClientV1("token") # No token required
    osu.set_osu_folder(OSU_FOLDER)
    beatmap_data = { beatmap.beatmap_id: {
        "taiko_sr_ratings": beatmap.taiko_sr_ratings,
        "audio_filename": beatmap.audio_filename,
    } for beatmap in osu.osu_db.map_list()}
    return beatmap_data

# Load raw beatmaps from .osu file
def get_beatmap_metadata(file):
    metadata = {}
    with open(file, "r") as f:
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
            metadata[category] = {}
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

import os
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


from multiprocessing import Pool
from math import ceil
from time import sleep
import shutil
def generate_beatmaps(arg):
    beatmap_data, beatmaps, thread_no = arg
    for i, (mapset, diffs) in enumerate(beatmaps):
        for (path, diff_file) in diffs:
            new_path = path.replace(OSU_FOLDER, NEW_OSU_FOLDER)
            metadata = get_beatmap_metadata(f"{path}\\{diff_file}")
            # Only process taiko maps
            if int(metadata["General"]["Mode"]) != 1:
                continue
            
            map_stars = beatmap_data[int(metadata["Metadata"]["BeatmapID"])]["taiko_sr_ratings"][0][1]
            if MIN_STARS > map_stars > MAX_STARS:
                continue

            # New File Format: Artist - Title (Creator) [Difficulty].osu
            new_diff_info = [(od, sv) for od in BEATMAP_OD for sv in BEATMAP_SV]
            diff_name = metadata["Metadata"]["Version"]
            for od,sv in new_diff_info:
                metadata["Metadata"]["Version"] = f"{diff_name} [OD{od}-SV{sv}]"
                metadata["Difficulty"]["OverallDifficulty"] = od
                metadata["Difficulty"]["SliderMultiplier"] = sv

                
                print(f"{path}\\{diff_file} ({metadata['Metadata']})")
                filename = f"{metadata['Metadata']['Artist']} - {metadata['Metadata']['Title']} ({metadata['Metadata']['Creator']}) [{metadata['Metadata']['Version']}].osu"
                invalid = '<>:"/\|?*'
                for char in invalid:
                    filename = filename.replace(char, '')
                
                os.makedirs(new_path, exist_ok=True)
                with open(f'{new_path}\\{filename}', "w+") as f:
                    map_data = update_beatmap_metadata(metadata)
                    f.writelines(map_data)
                
                if "AudioFilename" not in metadata["General"]:
                    continue
                shutil.copyfile(
                    f'{path}\\{metadata["General"]["AudioFilename"]}', 
                    f'{new_path}\\{metadata["General"]["AudioFilename"]}'
                )

        break

if __name__ == "__main__":
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















