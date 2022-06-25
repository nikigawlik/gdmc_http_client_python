#! /usr/bin/python3
"""### Generate a world of make-believe.

This file contains a comprehensive collection of functions designed
to introduce coders to the more involved aspects of the GDMC HTTP client.

The source code of this module contains examples for:

World Analysis:
- Global slices
- Biomes
- Obtrusiveness and optimal direction
- Versions
- Block categories

World manipulation:
- Interfaces
- Running commands
- Manipulating build area
- Placing blocks (advanced)
- Placing geometric shapes (advanced)
- Placing lecterns, signs, blocks with inventory

Utilities:
- 2D/3D loops
- Book writing

Optimisation:
- Keeping time
- Block caching
- Block buffering
- LRU Cache

If you haven't already, please take a look at Start_Here.py before continuing

NOTE: This file will be updated to reflect the latest features upon release
INFO: Should you have any questions regarding this software, feel free to visit
    the #ℹ-framework-support channel on the GDMC Discord Server
    (Invite link: https://discord.gg/V9MW65bD)

This file is not meant to be imported.
"""
__all__ = []
__author__ = "Blinkenlights"
__version__ = "v5.1_dev"
__date__ = "01 March 2022"

from copy import deepcopy
from time import time

from gdpc import geometry as geo
from gdpc import interface as intf
from gdpc import lookup
from gdpc.interface import globalinterface as gi
from gdpc.toolbox import flood_search_3D, loop2d

ALLOWED_TIME = 600  # permitted processing time in seconds (10 min)


# the grid resolution of sub-chunk searches
SUB_CHUNK_RES = 4

# custom default build area with override
STARTX, STARTY, STARTZ, ENDX, ENDY, ENDZ = 0, 0, 0, 999, 255, 999
if intf.requestBuildArea() != [0, 0, 0, 127, 255, 127]:
    STARTX, STARTY, STARTZ, ENDX, ENDY, ENDZ = intf.requestBuildArea()

GLOBALSLICE = intf.makeGlobalSlice()
XCHUNKSPAN, ZCHUNKSPAN = GLOBALSLICE.chunkRect[2], GLOBALSLICE.chunkRect[3]

chunk_info_template = {'designations': [], 'primary_biome': None, 'biomes': []}
chunk_info = [[deepcopy(chunk_info_template)
               for _ in range(ZCHUNKSPAN)]
              for _ in range(XCHUNKSPAN)]

# blocks to avoid (key is 3D coords)
# value may anything (e.g. reason for avoidance), since only the key is checked
to_avoid = {}

# waterways for checking connectivity to ocean and other bodies
# key is a position while value is the name (e.g. ocean, named river or lake)
# waterbody_info stores the biomes which it passes (key is identifier)
# e.g. 'ocean':{'connections': [], 'biomes_touching': [], 'biome_adjacent': []}
# waterbody_names is a lookup for the names of connected chunkwise bodies
# waterfalls stores the locations of waterfalls
RIVER_NAMES = ('Vindur', 'Slidr', 'Mjoll', 'Lifingr', 'Elyitsar', 'Moch',
               'Kerlnosar')
LAKE_NAMES = ()
FOREST_LAKE_NAMES = ()

waterways = {}
waterbody_info = {}
waterbody_names = {}
waterfalls = []


def chunk_biome_analysis():
    """Loop through all chunks in build area and identify biome traits."""
    for x, z in loop2d(XCHUNKSPAN, ZCHUNKSPAN):
        chunk_info[x][z]['primary_biome'] = GLOBALSLICE.getPrimaryBiomeNear(
            STARTX + x * 16, 0, STARTZ + z * 16)
        chunk_info[x][z]['biomes'] = GLOBALSLICE.getBiomesNear(STARTX + x * 16,
                                                               0,
                                                               STARTZ + z * 16)

        chunk_info[x][z]['designations'] = []

        # mark modifiers based on biomes (quicker than singular blocks)
        if 'snowy' in chunk_info[x][z]['primary_biome']:
            chunk_info[x][z]['designations'].append('snowy')

        if ('forest' in chunk_info[x][z]['primary_biome']
            or 'taiga' in chunk_info[x][z]['primary_biome']
            or 'grove' in chunk_info[x][z]['primary_biome']
                or 'wooded' in chunk_info[x][z]['primary_biome']):
            chunk_info[x][z]['designations'].append('forest')

        if ('ocean' in chunk_info[x][z]['primary_biome']
                or 'swamp' in chunk_info[x][z]['primary_biome']):
            chunk_info[x][z]['designations'].append('water')

        elif ('beach' in chunk_info[x][z]['primary_biome']
              or 'river' in chunk_info[x][z]['primary_biome']
              or 'shore' in chunk_info[x][z]['primary_biome']):
            chunk_info[x][z]['designations'].append('water-adjacent')

        if ('peaks' in chunk_info[x][z]['primary_biome']
            or 'hills' in chunk_info[x][z]['primary_biome']
            or 'mountains' in chunk_info[x][z]['primary_biome']
            or 'windswept' in chunk_info[x][z]['primary_biome']
                or 'eroded' in chunk_info[x][z]['primary_biome']):
            chunk_info[x][z]['designations'].append('harsh')

        elif ('plains' in chunk_info[x][z]['primary_biome']
              or 'meadow' in chunk_info[x][z]['primary_biome']
              or 'fields' in chunk_info[x][z]['primary_biome']
              or 'sparse' in chunk_info[x][z]['primary_biome']
              or 'plateau' in chunk_info[x][z]['primary_biome']
                or 'desert' in chunk_info[x][z]['primary_biome']):
            chunk_info[x][z]['designations'].append('flat')


def calculateTreelessHeightmap(worldSlice=GLOBALSLICE, interface=gi):
    heightmap = worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    area = worldSlice.rect

    for x, z in loop2d(area[2], area[3]):
        while True:
            y = heightmap[x, z]
            block = interface.getBlock(area[0] + x, y, area[1] + z)
            if (block[-4:] == '_log' or block[-7:] == '_leaves'
                    or block in lookup.AIR):
                heightmap[x, z] -= 1
            else:
                break

    return heightmap


def burial_site(population):
    """Generate the burial site based on the population size."""
    # TODO: Place tumuli in burial grounds based on population
    pass


def docks():
    # TODO: Docks with ships out at sea
    pass


if __name__ == '__main__':
    start = time()  # the time this code started in seconds

    def debug_chunk_info():
        conversion = {'snowy': 'snow_block', 'forest': 'oak_log',
                      'water': 'lapis_block', 'water-adjacent': 'lapis_ore',
                      'harsh': 'stone', 'flat': 'grass_block',
                      'structure': 'gold_block'}

        for x, z in loop2d(len(chunk_info), len(chunk_info[0])):
            blocks = [conversion[d] for d in chunk_info[x][z]['designations']]
            if blocks == []:
                blocks = 'redstone_block'
            geo.placeVolume(STARTX + x * 16 + 7, 250, STARTZ + z * 16 + 7,
                            STARTX + x * 16 + 10, 250, STARTZ + z * 16 + 10,
                            blocks)

        input('Enter to clear')
        geo.placeVolume(STARTX, 250, STARTZ, ENDX - 1, 250, ENDZ - 1, 'air')

    # define regions
    # - landing site/docks (ocean, river bank, hills/mountains, forest)
    # - burial grounds (flat chunks, edge of village)
    # - village center
    # - forestry
    # - quarry/mine
    # - agriculture (soil, water or irrigation)
    # - special points (highest, lava)

    # activate block caching to speed up requests
    gi.setCaching(True)

    # 16x16 chunk resolution analyses
    chunk_biome_analysis()

    # fine terrain analysis
    heightmap = calculateTreelessHeightmap()

    # 4x4-resolution block analysis for every chunk
    for cx, cz in loop2d(len(chunk_info), len(chunk_info[0])):
        chunkstart = intf.buildlocal2global(cx * 16, 0, cz * 16)
        chunkend = intf.buildlocal2global(cx * 16 + 16, 255, cz * 16 + 16)
        overlap_chunkstart = chunkstart[0] - \
            1, chunkstart[1], chunkstart[2] - 1
        overlap_chunkend = chunkend[0] + 1, chunkend[1], chunkend[2] + 1
        obs_struc = []
        obs_fluid = []

        # scan through the corner of every subchunk
        for jx, jz in loop2d(SUB_CHUNK_RES, SUB_CHUNK_RES):
            localx = cx * 16 + jx * SUB_CHUNK_RES
            localz = cz * 16 + jz * SUB_CHUNK_RES
            globalx, _, globalz = intf.buildlocal2global(localx, 0, localz)
            y = heightmap[localx][localz]
            if (intf.getBlock(globalx, y, globalz) in lookup.ARTIFICIAL
                    and (globalx, y, globalz) not in to_avoid):
                if 'structure' not in chunk_info[cx][cz]['designations']:
                    chunk_info[cx][cz]['designations'] += ['structure']
                result, newly_obs = flood_search_3D(globalx, y,
                                                    globalz,
                                                    *chunkstart,
                                                    *chunkend,
                                                    lookup.ARTIFICIAL,
                                                    observed=obs_struc,
                                                    diagonal=True)
                obs_struc += newly_obs
                for rx, ry, rz in result:
                    to_avoid[(rx, ry, rz)] = "Artificial structure detected"
            elif (intf.getBlock(globalx, y, globalz) in lookup.FLUID
                    and (globalx, y, globalz) not in waterways):
                if 'water' not in chunk_info[cx][cz]['designations']:
                    chunk_info[cx][cz]['designations'] += ['water']
                result, newly_obs = flood_search_3D(globalx, y,
                                                    globalz,
                                                    *overlap_chunkstart,
                                                    *overlap_chunkend,
                                                    lookup.FLUID,
                                                    observed=obs_fluid)
                obs_fluid += newly_obs

                pbiome = chunk_info[cx][cz]['primary_biome']
                if 'ocean' == pbiome[-5:]:
                    name = f'ocean-{cx}-{cz}'
                elif 'river' == pbiome:
                    name = f'river-{cx}-{cz}'
                elif 'swamp' == pbiome[:5]:
                    name = f'swamp-{cx}-{cz}'
                else:
                    if len(result) < 256:
                        name = f'pond-{cx}-{cz}'
                    else:
                        name = f'lake-{cx}-{cz}'

                waterbody_info[name] = {'connections': [],
                                        'biomes_touching': [],
                                        'biome_adjacent': []}
                for rx, ry, rz in result:
                    if (rx, ry, rz) in waterways:
                        if (waterways[(rx, ry, rz)]
                                not in waterbody_info[name]['connections']):
                            waterbody_info[name]['connections'] += [
                                waterways[(rx, ry, rz)]
                            ]
                    else:
                        waterways[(rx, ry, rz)] = name
                        biomes = chunk_info[cx][cz]['biomes']
                        waterbody_info[name]['biomes_touching'] = biomes
                        surrounding = []

                        surrounding += \
                            chunk_info[cx + 1][cz + 1]['primary_biome'] + \
                            chunk_info[cx - 1][cz + 1]['primary_biome'] + \
                            chunk_info[cx + 1][cz - 1]['primary_biome'] + \
                            chunk_info[cx - 1][cz - 1]['primary_biome']

    input(waterbody_info.keys())

    debug_chunk_info()

    gi.setCaching(False)

    # # start construction
    # troglo_cave_coords = troglo_cave()
    #
    # center_coords = village_center()
    # camp_coords = camp()
    # mine_coords = mine()

    # generate more until 60 seconds remain
    while time() - start <= ALLOWED_TIME - 60:
        break

    # cleanup and presentation

    population = 0
    troglo_grave_coords = burial_site(population)

    # if docks_coords is None:
    #     landing_site()
    #
    # chronicle()
