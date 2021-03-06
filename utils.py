import collections
import copy
import errno
import json
import os
import socket

import mcstatus as mcs
from discord import Embed

database_filename = 'database.json'


class MCServer:
    pass

def remove_unused(db, guild, channel):
    if len(db[guild][channel]) == 0:
        db[guild].pop(channel)
        if len(db[guild]) == 0:
            db.pop(guild)


# TODO: encapsulate all server info into separate MCServer class
def status_message_generator(server_list):
    embed = Embed()
    for server in server_list:
        mcserver = mcs.MinecraftServer.lookup(server)
        try:
            status = mcserver.status()
        except (socket.gaierror, socket.timeout) as e:
            status = "-"
        except socket.error as e:
            status = "-"
            if e.errno == errno.EPIPE:
                print("Pipe error!")

        try:
            playerlist = mcserver.query()
        except (socket.gaierror, socket.timeout) as e:
            playerlist = "-"
        except socket.error as e:
            playerlist = "-"
            if e.errno == errno.EPIPE:
                print("Pipe error!")

        if status == "-":
            indicator = ":black_circle: "
            description = '-'
        else:
            if status.players.online < status.players.max:
                indicator = ":large_blue_circle: "
            else:
                indicator = ":red_circle: "
            if type(status.description) is str:
                description = status.description
            else:
                description = status.description["text"]
        playerlist_string = "\n"
        if playerlist != '-':
            if len(playerlist.players.names) == 0:
                playerlist_string += "__No players online__"
            else:
                playerlist_string += "__Online players:__\n"
                playerlist_string += ", ".join(str(x) for x in playerlist.players.names)
        else:
            playerlist_string += "__Player list unavailable__"
        embed.add_field(
            name=f"{indicator} **{server}**\n{(description if status != '-' else '-')}",
            value=f"{status.players.online}/{str(status.players.max) + playerlist_string}" if status != '-' else "-"
        )
    return embed


def generate_message_link_list(message_database, ctx, client):
    response = ""
    associated_messages = []
    for channel, channel_dict in message_database[str(ctx.guild.id)].items():
        response += f"Messages in {client.get_channel(int(channel)).mention}:\n"
        for message in channel_dict:
            monitored_message = f"https://discordapp.com/channels/{ctx.guild.id}/{channel}/{message}"
            associated_messages.append((str(ctx.guild.id), str(channel), str(message)))
            response += f"Message #{len(associated_messages)} {monitored_message}\n"
    return response, associated_messages


def read_database():
    if not os.path.exists(database_filename):
        f = open(database_filename, 'w+')
        f.write('{}')
        f.close()
    with open(database_filename, "r") as f:
        message_database = json.load(f)
    return message_database


def write_database(db):
    with open(database_filename, 'w+') as f:
        json.dump(db, f)


def deep_dict_merge(dct1, dct2, override=True) -> dict:
    merged = copy.deepcopy(dct1)
    for k, v2 in dct2.items():
        if k in merged:
            v1 = merged[k]
            if isinstance(v1, dict) and isinstance(v2, collections.Mapping):
                merged[k] = deep_dict_merge(v1, v2, override)
            elif isinstance(v1, list) and isinstance(v2, list):
                merged[k] = v1 + v2
            else:
                if override:
                    merged[k] = copy.deepcopy(v2)
        else:
            merged[k] = copy.deepcopy(v2)
    return merged
