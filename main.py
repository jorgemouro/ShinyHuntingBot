import discord
from discord.ext import commands
import json
import os  # Para trabajar con rutas
import signal
import asyncio
import requests  # Para hacer solicitudes HTTP a la PokeAPI
import webserver

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Crea una instancia del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para almacenar las listas de shiny hunts de los usuarios
shiny_hunts = {}

# Ruta del archivo JSON (cambia a tu ruta)
json_file_path = r"C:\Users\yor\Desktop\bot\shiny_hunts.json"  # Cambia la ruta si es necesario

# Función para guardar las listas en el archivo JSON
def save_shiny_hunts():
    # Verifica si la carpeta existe, si no, la crea
    folder_path = os.path.dirname(json_file_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)  # Crea la carpeta si no existe

    # Guarda el archivo shiny_hunts.json
    try:
        with open(json_file_path, "w") as f:
            json.dump(shiny_hunts, f)
        print("Shiny Hunts list saved to file.")
    except Exception as e:
        print(f"Error saving file: {e}")

# Función para decorar los mensajes
def decorate_message(msg):
    return f"🎉 ✨ {msg} 🎉"

# Función para obtener emoji por tipo de Pokémon
def get_pokemon_emoji(hunt_type):
    type_emojis = {
        "fire": "🔥",  # Fuego
        "water": "💧",  # Agua
        "bug": "🐛",    # Bicho
        "dragon": "🐉",  # Dragón
        "electric": "⚡",  # Eléctrico
        "ghost": "👻",   # Fantasma
        "fairy": "🧚",   # Hada
        "ice": "❄️",     # Hielo
        "fighting": "🥊",  # Lucha
        "normal": "⚪",    # Normal
        "grass": "🌿",    # Planta
        "psychic": "🧠",   # Psíquico
        "rock": "⛰️",    # Roca
        "dark": "🌑",     # Siniestro
        "ground": "🌍",   # Tierra
        "poison": "☠️",   # Veneno
        "flying": "🦅",   # Volador
    }
    return type_emojis.get(hunt_type, "❓")  # Retorna un emoji predeterminado si no se encuentra el tipo

# Función para obtener el tipo de Pokémon desde la PokeAPI
def get_pokemon_type(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        types = [t['type']['name'] for t in data['types']]
        return types
    else:
        return None  # Si no se encuentra el Pokémon

# Comando para ver el Shiny Hunt de un usuario
@bot.command()
async def shinylist(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author  # Si no se pasa un usuario, se muestra la lista del que ejecuta el comando

    if str(member.id) not in shiny_hunts:
        shiny_hunts[str(member.id)] = []  # Crea la lista si no existe

    if shiny_hunts[str(member.id)]:
        hunts = "\n".join([f"{hunt[0]} {get_pokemon_emoji(hunt[1])} ({hunt[1]})" for hunt in shiny_hunts[str(member.id)]])  # Mostrar tipo de shiny con emoji
        await ctx.send(decorate_message(f"{member.display_name}'s Shiny Hunts list:\n{hunts}"))
    else:
        await ctx.send(decorate_message(f"{member.display_name} has no Shiny Hunts in their list."))

# Comando para ver todos los usuarios con listas de Shiny Hunts
@bot.command()
async def allshiny(ctx):
    users_with_hunts = [f"<@{user_id}>" for user_id in shiny_hunts if shiny_hunts[user_id]]  # Lista de usuarios con Shiny Hunts
    if users_with_hunts:
        await ctx.send(decorate_message(f"Users with Shiny Hunts: {', '.join(users_with_hunts)}"))
    else:
        await ctx.send(decorate_message("No users have Shiny Hunts in their lists."))

# Comando para agregar un Shiny Hunt
@bot.command()
async def addshiny(ctx, *, hunt: str):
    user = ctx.author
    if str(user.id) not in shiny_hunts:
        shiny_hunts[str(user.id)] = []  # Crea la lista si no existe

    # Obtener los tipos del Pokémon usando PokeAPI
    pokemon_types = get_pokemon_type(hunt)

    if pokemon_types:
        hunt_type = "Singles"  # Asumimos que el hunt es tipo "Singles" por defecto
        for pokemon_type in pokemon_types:
            shiny_hunts[str(user.id)].append((hunt, pokemon_type))  # Añade el Shiny Hunt con su tipo
        save_shiny_hunts()  # Guarda el archivo JSON
        await ctx.send(decorate_message(f"✅ You have added the Shiny Hunt '{hunt}' {get_pokemon_emoji(pokemon_types[0])} ({', '.join(pokemon_types)}) to your list!"))
    else:
        await ctx.send(decorate_message(f"❌ The Pokémon '{hunt}' could not be found. Please make sure the name is correct."))

# Comando para eliminar un Shiny Hunt
@bot.command()
async def removeshiny(ctx, *, hunt: str):
    user = ctx.author
    if str(user.id) not in shiny_hunts or hunt not in [h[0] for h in shiny_hunts[str(user.id)]]:
        await ctx.send(decorate_message(f"❌ You don't have the Shiny Hunt '{hunt}' in your list."))
    else:
        shiny_hunts[str(user.id)] = [h for h in shiny_hunts[str(user.id)] if h[0] != hunt]  # Elimina el shiny hunt
        save_shiny_hunts()  # Guarda el archivo JSON
        await ctx.send(decorate_message(f"✅ You have removed the Shiny Hunt '{hunt}' from your list!"))

# Comando para mostrar el número total de shiny hunts
@bot.command()
async def totalshiny(ctx):
    user = ctx.author
    if str(user.id) not in shiny_hunts or not shiny_hunts[str(user.id)]:
        await ctx.send(decorate_message(f"❌ You have no Shiny Hunts in your list."))
    else:
        total = len(shiny_hunts[str(user.id)])
        await ctx.send(decorate_message(f"🔢 You have a total of {total} Shiny Hunts in your list."))

# Comando para limpiar todos los Shiny Hunts de un usuario
@bot.command()
async def cleanshiny(ctx):
    user = ctx.author
    if str(user.id) not in shiny_hunts or not shiny_hunts[str(user.id)]:
        await ctx.send(decorate_message(f"❌ You have no Shiny Hunts to clean."))
    else:
        shiny_hunts[str(user.id)] = []  # Limpia la lista
        save_shiny_hunts()  # Guarda el archivo JSON
        await ctx.send(decorate_message(f"🧹 All Shiny Hunts have been removed from your list!"))

# Comando para mostrar el mensaje de ayuda
@bot.command()
async def shinyhelp(ctx):
    help_message = (
        "✨ **!shinylist [@member]**\n"
        "Shows the Shiny Hunts list of the specified member. If no member is specified, shows your own list.\n\n"
        "➕ **!addshiny <hunt name>**\n"
        "Adds a shiny hunt to your list. The Pokémon type is automatically detected.\n\n"
        "➖ **!removeshiny <hunt name>**\n"
        "Removes a shiny hunt from your list.\n\n"
        "🔢 **!totalshiny**\n"
        "Shows the total number of shiny hunts in your list.\n\n"
        "🧹 **!cleanshiny**\n"
        "Clears all shiny hunts from your list.\n\n"
        "ℹ️ **!shinyhelp**\n"
        "Shows this help message with all available commands and their usage.\n\n"
        "👥 **!allshiny**\n"
        "Shows a list of all users who have at least one Shiny Hunt in their list."
    )
    await ctx.send(help_message)

# Cargar las listas de Shiny Hunts desde el archivo al iniciar el bot
def load_shiny_hunts():
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading file: {e}")
    return {}

shiny_hunts = load_shiny_hunts()

# Inicia el bot
webserver.keep_alive()
bot.run(DISCORD_TOKEN)