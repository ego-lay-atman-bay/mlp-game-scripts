from .cli import CLI, CLICommand
from typing import Literal
from dataclasses import dataclass
from ..console import console

def sqlrepr(value: str | int | float | None):
    if value is None:
        return 'NULL'
    elif isinstance(value, (int, float)):
        return repr(value)
    elif isinstance(value, str):
        return f'"{value.replace('"', '""')}"'
    
    raise NotImplementedError(f'Cannot get sqlrepr for "{value}" of type {type(value)}')

LOCATIONS = {
    0: 'STR_PONYVILLE',
    1: 'STR_CANTERLOT',
    2: 'STR_SWEET_APPLE_ACRES',
    3: 'STR_EVERFREE_FOREST',
    4: 'STR_CRYSTAL_EMPIRE',
    5: 'STR_CRYSTAL_EMPIRE',
    6: 'STR_KLUGETOWN',
}

@dataclass
class PonyRecord:
    id: str
    name: str
    description: str
    stars: int
    location: Literal[
        'Ponyville',
        'Sweet Apple Acres',
        'Canterlot',
        'Crystal Empire',
        'Klugetown',
    ] | None
    house: str
    pro: str | None
    alternate_form: str | None
    minigame_cooldown: int | None

    def __str__(self) -> str:
        values = [
            sqlrepr(self.id),
            sqlrepr(self.name),
            sqlrepr(self.description),
            sqlrepr(self.stars),
            sqlrepr(self.location),
            sqlrepr(self.house),
            sqlrepr(self.pro),
            sqlrepr(self.alternate_form),
            sqlrepr(self.minigame_cooldown),
        ]

        return f"INSERT INTO Ponies VALUES ({', '.join(values)});"


@CLI.register_command
class SQLInventoryCommand(CLICommand):
    COMMAND = 'sql_inventory'
    HELP = 'Create an SQL database script with all your ponies'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            'code',
            help = 'Friend code',
        )
        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            help = 'Output sql file',
            required = True,
        )
    
    def run_command(self):
        import os
        import json
        import requests
        from textwrap import dedent
        from luna_kit.gameobjectdata import GameObjectData
        from luna_kit.loc import LOC
        from luna_kit.typings.defaultGameCampaign import DefaultGameCampaignType

        console.print('Getting inventory')
        inventory_request = requests.get(
            f"https://all-the-ponies-api.vercel.app/save/{self.args.code}/inventory/"
        )
        try:
            inventory_request.raise_for_status()
        except requests.HTTPError as e:
            e.add_note(inventory_request.text)
            raise e
        
        inventory = inventory_request.json()

        console.print('loading gameobjectdata.xml')
        gameobjectdata = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))
        console.print('loading english.loc')
        locale = LOC(os.path.join(self.args.game_folder, 'english.loc'))
        console.print('loading defaultGameCampaign.json')
        with open(os.path.join(self.args.game_folder, 'defaultGameCampaign.json'), 'r') as file:
            defaultGameCampaign: DefaultGameCampaignType = json.load(file)
        
        random_pros: list[str] = defaultGameCampaign.get('group_quests', {}).get('random_pros')

        console.print('loading groupquests.json')
        with open(os.path.join(self.args.game_folder, 'groupquests.json'), 'r') as file:
            group_quests = json.load(file)
        
        fixed_pros: dict[str, list[str]] = {}
        for  quest in group_quests.values():
            quest: dict
            name = locale.translate(quest['Name'])

            for story_point in quest.get('StoryPoints', []):
                story_point: dict
                if story_point.get('PremiumPony'):
                    fixed_pros.setdefault(name, []).append(story_point['PremiumPony'])
        
        
        def is_pro(pony_id: str):
            if pony_id in random_pros:
                return 'Random'
            
            for quest_name, pros in fixed_pros.items():
                if pony_id in pros:
                    return quest_name
            
            return None

        
        ponies: list[PonyRecord] = []

        console.print('creating database')
        for save_info in inventory['inventory']['ponies']:
            pony_id = save_info['id']
            pony = gameobjectdata.get_object(pony_id)
            house = gameobjectdata.get_object(
                pony.get('House', {}).get('Type')
            )

            minigame_cooldown: int | None = pony.get('Minigames', {}).get('TimeBetweenPlayActions', 0)

            if int(pony.get('AI', {}).get('Max_Level', '0')):
                minigame_cooldown = None
            
            pony_command = PonyRecord(
                id = pony_id,
                name = locale.translate(pony.get('Name', {}).get('Unlocal', pony_id)),
                description = locale.translate(pony.get('Description', {}).get('Unlocal', pony_id)),
                stars = save_info.get('level', 0),
                location = locale.translate(LOCATIONS.get(
                    pony.get('House', {}).get('HomeMapZone', ''),
                    None,
                )).title(),
                house = locale.translate(
                    house.get('Name', {}).get('Unlocal', house.id),
                ),
                pro = is_pro(pony_id),
                alternate_form = pony.get('IsChangelingWithSet', {}).get('AltPony', None) or None,
                minigame_cooldown = minigame_cooldown,
            )

            ponies.append(pony_command)

        sql_script = dedent("""\
        -- A database of all the ponies I have in the MLP game (there's over 2k in the game)

        DROP TABLE IF EXISTS Ponies;

        CREATE TABLE Ponies (
            ID TEXT PRIMARY KEY,
            Name TEXT NOT NULL,
            Description TEXT,
            Stars INT CHECK (Stars >= 0 AND Stars <= 5) DEFAULT 0,
            Location TEXT CHECK (
                Location == "Ponyville" OR
                Location == "Sweet Apple Acres" OR
                Location == "Canterlot" OR
                Location == "Crystal Empire" OR
                Location == "Klugetown"
            ),
            House TEXT,
            Pro TEXT,
            AlternateForm TEXT,
            MinigameCooldown INT
        );

        """)

        sql_script += '\n'.join(str(row) for row in ponies)

        output = os.path.abspath(self.args.output)
        os.makedirs(os.path.dirname(output), exist_ok = True)
        with open(output, 'w', encoding = 'utf-8') as file:
            file.write(sql_script)
        
        console.print(f'saved to "{self.args.output}"')

