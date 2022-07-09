## File Format

General Structure
- **\[TEXT_CONTENT\]**: File Section
- **TEXT_CONTENT:**: Attribute Value  

Important values

\[General\]
- Taiko Map: Mode: 1 
- AudioFilename
- 

\[Metadata\]
- Difficulty Name: Version: TEXT_CONTENT
- BeatmapID, BeatmapSetID 

\[Difficulty\]
- HPDrainRate
- OverallDifficulty
- SliderMultiplier

## Osu-Tools Properties

- self.beatmap_id = int(map_info['beatmap_id'])
- self.mapset_id = int(map_info['beatmapset_id'])
- self.audio_filename = map_info["audio_filename"]
- self.taiko_sr_ratings = map_info["taiko_star_ratings"]
