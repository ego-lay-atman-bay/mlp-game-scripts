from .cli import CLI, CLICommand
from ..console import console

@CLI.register_command
class StatsCommand(CLICommand):
    COMMAND = 'stats'
    HELP = 'Get pony stats'

    @classmethod
    def build_args(cls, parser):
        pass
    
    def run_command(self):
        from luna_kit.gameobjectdata import GameObjectData
        import os

        data = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))

        ponies = []
        npc_ponies = []
        friends = {}
        changelings = []
        critters = [
            'Pony_Crit_SAA_Sheep',
            'Pony_Crit_SAA_Sheep_Cute',
            'Pony_Crit_Rabbit_Brown',
            'Pony_Crit_Rabbit_White',
            'Pony_Crit_SAA_Pig',
            'Pony_Crit_SAA_Pig_Dirty',
            'Pony_Crit_SAA_Cow_Basic',
            'Pony_Crit_SAA_Cow_Upgrade',
            'Pony_Crit_SAA_Chicken_Basic',
            'Pony_Crit_SAA_Chicken_Upgrade',
        ]
        unused_ponies = [
            'Pony_Twilight_Sneak_Le',
            'Pony_Camo_Dash',
            'Pony_Wingless_Rainbow_Dash',
            'Pony_Crystal_Luna_Hair_Test',
            'Pony_Token_Test',
        ]
        quest_ponies = [
            'Pony_Quest_Duplicate_Starlight',
            'Pony_Quest_Duplicate_Thorax',
            'Pony_Quest_Duplicate_Discord',
            'Pony_Quest_Duplicate_Trixie',
            'Pony_Quest_Fluttershy_Duplicate',
            'Pony_Quest_Duplicate_Scootaloo',
            'Pony_Quest_Duplicate_Sweetiebelle',
            'Pony_Quest_Duplicate_Apple_Bloom',
            'Pony_Quest_Changeling_Runaway_01',
            'Pony_Quest_Changeling_Runaway_02',
        ]

        for hidden_pony in data['HiddenPony'].values():
            pony_id = hidden_pony.get('Parent', {}).get('PonyName')
            if pony_id and pony_id not in npc_ponies:
                npc_ponies.append(pony_id)
        
        for pony in data['Pony'].values():
            if pony.id in changelings:
                continue
            if pony.id in npc_ponies:
                continue
            if pony.id in unused_ponies:
                continue
            if pony.id in quest_ponies:
                continue
            if pony.id in critters:
                continue
            
            is_friend = False
            for pony_friends in friends.values():
                if pony.id in pony_friends:
                    is_friend = True
                    break
            
            if is_friend:
                continue

            changeling = pony.get('IsChangelingWithSet', {}).get('AltPony', None)
            if changeling is not None:
                changelings.append(changeling)
                continue

            pony_friends = [friend for friend in pony.get('Friends', {}).get('Friend', []) if friend]
            if len(pony_friends):
                friends[pony.id] = pony_friends
                for friend in pony_friends:
                    if friend in ponies:
                        ponies.remove(friend)
                    
                continue
                    

            ponies.append(pony.id)
        
        stats = {
            'ponies': len(ponies),
            'changelings': len(changelings),
            'friend_parents': len(friends),
            'friends': sum([len(friend) for friend in friends.values()]),
            'npc': len(npc_ponies),
            'unused': len(unused_ponies),
            'quest': len(quest_ponies),
            'critters': len(critters),
        }
        
        console.print('[b green]Ponies stats[/]')
        console.print(f"[yellow]ponies: [blue]{stats['ponies']}[/]")
        console.print(f"[yellow]changelings: [blue]{stats['changelings']}[/]")
        console.print(f"[yellow]friend_parents: [blue]{stats['friend_parents']}[/]")
        console.print(f"[yellow]friends: [blue]{stats['friends']}[/]")
        console.print(f"[yellow]npc: [blue]{stats['npc']}[/]")
        console.print(f"[yellow]unused: [blue]{stats['unused']}[/]")
        console.print(f"[yellow]quest: [blue]{stats['quest']}[/]")
        console.print(f"[yellow]critters: [blue]{stats['critters']}[/]")
        
        console.print(f'[yellow]total: [blue]{sum(stats.values()) + stats['changelings']}[/]')
