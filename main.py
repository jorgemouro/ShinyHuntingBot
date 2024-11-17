import discord
from discord.ext import commands
import json
import os  # Para trabajar con rutas
import signal
import asyncio
import requests  # Para hacer solicitudes HTTP a la PokeAPI
import webserver
import random

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


@bot.command()
@commands.has_permissions(administrator=True)  # Solo los administradores pueden usar este comando
async def clearuserlist(ctx, member: discord.Member):
    if str(member.id) in shiny_hunts:
        shiny_hunts[str(member.id)] = []  # Limpia la lista del usuario
        save_shiny_hunts()  # Guarda el archivo JSON
        await ctx.send(decorate_message(f"🧹 The Shiny Hunt list of {member.display_name} has been cleared!"))
    else:
        await ctx.send(decorate_message(f"❌ {member.display_name} has no Shiny Hunt list to clear."))


@bot.command()
async def randomhunt(ctx):
    # Lista de Pokémon aleatorios para el hunt
    random_pokemons = ["Pikachu", "Charizard", "Bulbasaur", "Squirtle", "Eevee", "Snorlax"]
    random_pokemon = random.choice(random_pokemons)
    
    # Obtiene los tipos del Pokémon
    pokemon_types = get_pokemon_type(random_pokemon)

    if pokemon_types:
        # Agrega el hunt a la lista del usuario
        user = ctx.author
        if str(user.id) not in shiny_hunts:
            shiny_hunts[str(user.id)] = []

        shiny_hunts[str(user.id)].append((random_pokemon, pokemon_types))
        save_shiny_hunts()
        await ctx.send(decorate_message(f"✅ You have added a random Shiny Hunt for '{random_pokemon}' {get_pokemon_emoji(pokemon_types[0])} ({', '.join(pokemon_types)}) to your list!"))
    else:
        await ctx.send(decorate_message(f"❌ Could not fetch details for the Pokémon '{random_pokemon}'."))

@bot.command()
async def completehunt(ctx, *, hunt: str):
    user = ctx.author
    
    if str(user.id) not in shiny_hunts or hunt not in [h[0] for h in shiny_hunts[str(user.id)]]:
        await ctx.send(f"❌ You don't have a Shiny Hunt for '{hunt}' in your list.")
        return
    
    hunt_data = next(h for h in shiny_hunts[str(user.id)] if h[0] == hunt)
    
    if 'completed' in hunt_data:
        await ctx.send(f"❌ The Shiny Hunt for '{hunt}' is already marked as completed.")
    else:
        hunt_data.append('completed')
        save_shiny_hunts()
        await ctx.send(f"✅ The Shiny Hunt for '{hunt}' has been marked as completed!")
    
@bot.command()
async def shinylist(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author  # Si no se pasa un usuario, se muestra la lista del que ejecuta el comando

    if str(member.id) not in shiny_hunts:
        shiny_hunts[str(member.id)] = []

    if shiny_hunts[str(member.id)]:
        hunts = "\n".join([f"{hunt[0]} {', '.join([get_pokemon_emoji(t) for t in hunt[1]])} ({', '.join(hunt[1])})" + (" ✅ Completed" if 'completed' in hunt else "") for hunt in shiny_hunts[str(member.id)]])
        await ctx.send(f"{member.display_name}'s Shiny Hunts list:\n{hunts}")
    else:
        await ctx.send(f"{member.display_name} has no Shiny Hunts in their list.")

# Comando para ver todos los usuarios con listas de Shiny Hunts
@bot.command()
async def allshiny(ctx):
    if not shiny_hunts:
        await ctx.send("❌ No one has any Shiny Hunts.")
        return

    all_hunts = ""
    for user_id, hunts in shiny_hunts.items():
        user = await bot.fetch_user(user_id)
        if hunts:
            hunts_list = "\n".join([f"{hunt[0]} {', '.join([get_pokemon_emoji(t) for t in hunt[1]])} ({', '.join(hunt[1])})" + (" ✅ Completed" if 'completed' in hunt else "") for hunt in hunts])
            all_hunts += f"{user.display_name}:\n{hunts_list}\n\n"
        else:
            all_hunts += f"{user.display_name}: No Shiny Hunts.\n\n"
    
    await ctx.send(f"✨ **All Shiny Hunts**:\n{all_hunts}")
    
# Comando para agregar un Shiny Hunt
@bot.command()
async def addshiny(ctx, *, hunt: str):
    user = ctx.author
    if str(user.id) not in shiny_hunts:
        shiny_hunts[str(user.id)] = []

    pokemon_types = get_pokemon_type(hunt)

    if pokemon_types:
        hunt_type = "Singles"

        found = False
        for existing_hunt in shiny_hunts[str(user.id)]:
            if existing_hunt[0] == hunt:
                existing_hunt[1].extend([t for t in pokemon_types if t not in existing_hunt[1]])
                found = True
                break
        
        if not found:
            shiny_hunts[str(user.id)].append((hunt, pokemon_types))

        save_shiny_hunts()
        await ctx.send(f"✅ You have added the Shiny Hunt '{hunt}' {', '.join([get_pokemon_emoji(t) for t in pokemon_types])} ({', '.join(pokemon_types)}) to your list!")
    else:
        await ctx.send(f"❌ The Pokémon '{hunt}' could not be found. Please make sure the name is correct.")

# Comando para eliminar un Shiny Hunt
@bot.command()
async def removeshiny(ctx, *, hunt: str):
    user = ctx.author
    if str(user.id) not in shiny_hunts or hunt not in [h[0] for h in shiny_hunts[str(user.id)]]:
        await ctx.send(f"❌ You don't have the Shiny Hunt '{hunt}' in your list.")
    else:
        shiny_hunts[str(user.id)] = [h for h in shiny_hunts[str(user.id)] if h[0] != hunt]
        save_shiny_hunts()
        await ctx.send(f"✅ You have removed the Shiny Hunt '{hunt}' from your list!")

# Comando para mostrar el número total de shiny hunts
@bot.command()
async def totalshiny(ctx):
    user = ctx.author
    if str(user.id) not in shiny_hunts or not shiny_hunts[str(user.id)]:
        await ctx.send(f"❌ You have no Shiny Hunts in your list.")
    else:
        total = len(shiny_hunts[str(user.id)])
        await ctx.send(f"🔢 You have a total of {total} Shiny Hunts in your list.")

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
        "✅ **!completehunt <hunt name>**\n"
        "Marks a Shiny Hunt as completed without removing it from your list. Use this command when you catch the shiny Pokémon.\n\n"
        "🎲 **!random**\n"
        "Picks a random Shiny Hunt from your list.\n\n"
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