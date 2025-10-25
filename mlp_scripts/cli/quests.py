from typing import TYPE_CHECKING

from .cli import CLI, CLICommand

if TYPE_CHECKING:
    from luna_kit.questtable import Quest
    from luna_kit.cinematictable import Scene


PATHS = {
    'fullscale_twilight_sparkle_generic': 'Twilight Sparkle',
    'fullscale_princess_luna_generic_flipped': 'Princess Luna',
    'fullscale_applejack_generic_flipped': 'Applejack',
    'fullscale_applejack_generic': 'Applejack',
    'fullscale_princess_luna_generic': 'Princess Luna',
    'fullscale_fluttershy_generic': 'Fluttershy',
    'fullscale_fluttershy_generic_flipped': 'Fluttershy',
    'fullscale_rainbow_dash_generic': 'Rainbow Dash',
    'fullscale_rainbow_dash_generic_flipped': 'Rainbow Dash',
    'fullscale_rarity_generic': 'Rarity',
    'fullscale_rarity_generic_flipped': 'Rarity',
    'gui/gnr_img_questgiver_celestia.png': 'Princess Celestia',
    'fullscale_princess_celestia_generic': 'Princess Celestia',
    'fullscale_spike_generic': 'Grown-Up Spike',
    'fullscale_twilight_sparkle_generic_flipped': 'Twilight Sparkle',
    'fullscale_pinkie_pie_generic': 'Pinkie Pie',
    'fullscale_starlight_glimmer_generic_flipped': 'Starlight Glimmer',
    'fullscale_twist_generic': 'Twist',

    'gui/gnr_img_questgiver_applejack.png': 'Applejack',
    'gui/gnr_img_questgiver_fluttershy.png': 'Fluttershy',
    'gui/g_l_q.png': 'Princess Luna',
    'gui/gnr_img_questgiver_twilightsparkle_pri.png': 'Twilight Sparkle',
    'gui/gnr_img_questgiver_rainbowdash.png': 'Rainbow Dash',
    'gui/gnr_img_questgiver_rarity.png': 'Rarity',
    'gui/gnr_img_questgiver_pinkypie.png': 'Pinkie Pie',
}


@CLI.register_command
class QuestCommand(CLICommand):
    COMMAND = 'questline'
    HELP = 'Generate wiki page for quest line'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            '-c', '--category', '--categories',
            dest = 'categories',
            help = 'Quest categories',
            nargs = '+',
            required = True,
        )
        
        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            required = True,
            help = 'Output file',
        )

    def run_command(self):
        import os
        import json

        from ..console import console
        from ..utils import find_first
        
        from luna_kit.gameobjectdata import GameObjectData
        from luna_kit.loc import LOC
        from luna_kit.questtable import QuestTable
        from luna_kit.cinematictable import CinematicTable
        from luna_kit.xml import parse_xml
        from luna_kit.typings import DefaultGameCampaignType

        self.gameobjectdata = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))
        
        with open(os.path.join(self.args.game_folder, 'defaultGameCampaign.json'), 'r') as file:
            defaultGameCampaign: DefaultGameCampaignType = json.load(file)
        
        with open(os.path.join(self.args.game_folder, 'ponytasks.json'), 'r') as file:
            ponytasks: dict[str, list[dict[str, str | int]]] = json.load(file)
        
        self.ponytasks: dict[str, dict[str, str | int]] = {}

        for task in ponytasks['PonyTasks']:
            self.ponytasks[task['ID']] = task.copy()
        
        for task in defaultGameCampaign['PonyTaskData']:
            self.ponytasks[task['ID']].update(task)

        self.loc = LOC(os.path.join(self.args.game_folder, 'english.loc'))

        self.questtable = QuestTable(os.path.join(self.args.game_folder, 'questtable.xml'))
        self.cinematictable = CinematicTable(os.path.join(self.args.game_folder, 'cinematictable.xml'))

        questlines: list[list[Quest]] = []

        for category in self.args.categories:
            quests = self.get_category(category)
            requirements = quests[0].requirements.quests_completed
            last_index = -1
            for requirement in requirements:
                for i, questline in enumerate(questlines):
                    if find_first(questline, lambda quest: quest.name == requirement):
                        last_index = max(last_index, i)
            
            if last_index <= -1:
                last_index = len(questlines) - 1
            
            questlines.insert(last_index + 1, quests)
        
        result = ''
        for questline in questlines:
            console.print(questline[0].category)
            console.print(questline[0].requirements.quests_completed)
            result += self.write_category(questline)
        
        output = os.path.abspath(self.args.output)
        os.makedirs(os.path.dirname(output), exist_ok = True)
        with open(output, 'w', encoding = 'utf-8') as file:
            file.write(result)

    def get_category(self, category: str):
        from ..utils import find_first
        from luna_kit.questtable import Quest

        quests = self.questtable.categories[category]
        result: list[Quest] = []

        for quest in quests.values():
            before = find_first(
                quest.requirements.quests_completed,
                lambda value: value in quests,
            )
            
            if before is None:
                result.insert(0, quest)
            else:
                other = find_first(
                    result,
                    lambda value: value.name == before,
                )
                if other:
                    result.insert(result.index(other) + 1, quest)
                else:
                    result.append(quest)
        
        return result
    
    def write_category(self, category: 'list[Quest]'):
        from textwrap import dedent
        from ..utils import traditional_round
        
        result = f"== {category[0].category} ==\n"

        for quest in category:
            quest_template = ''

            for event in quest.events.start:
                if event.type == 'PlayCinematic':
                    quest_template += '\n' + self.get_dialogue(self.cinematictable.get(event.value)) + '\n'

            quest_template += dedent(f"""
                {{{{Quest
                |name={self.loc.translate(quest.info.title)}
                |giver={self.path_to_name(quest.info.giver_image)}
                |intro={self.loc.translate(quest.info.description)}
                """)
            
            for i, task in enumerate(quest.task_list, 1):
                quest_template += f"|task{i}={self.loc.translate(task.description)}\n"
                if task.skippable:
                    quest_template += f"|skip{i}={{{{Item|Gem|amount={task.skip_cost}}}}}"
                    
                    if not task.no_skip_by_ads:
                        quest_template += f' or {traditional_round(task.skip_cost * 0.7)} ad watches'

                    quest_template += '\n'
                
                pony_task = ''
                for count in task.counts:
                    match count.category:
                        case 'CompleteTask':
                            pony_task = self.ponytasks[count.sub_object]
                            quest_template += f"|timer{i}={pony_task['Duration']}\n"
                    
                    # if count.value > 1:
                    quest_template += f'|times{i}={count.value:,}\n'
                
            
            quest_template += f"|xp={quest.rewards.xp}\n"
            if quest.rewards.bits:
                quest_template += f"|bit={quest.rewards.bits}\n"
            if quest.rewards.gems:
                quest_template += f"|gem={quest.rewards.gems}\n"
            if quest.rewards.item.id:
                reward = quest.rewards.item.id
                reward_obj = self.gameobjectdata.get_object(reward)
                if reward_obj is not None and reward_obj.category == 'Pony':
                    name = self.loc.translate(reward_obj.get('Name', {}).get('Unlocal', reward_obj.id))
                    reward = f'[[File:{name} portrait.png]]'
                
                quest_template += f"|reward={reward}\n"
                if quest.rewards.item.alt_value:
                    quest_template += f'|alt_reward={quest.rewards.item.alt_value}\n'
            quest_template += f"|outro={self.loc.translate(quest.info.complete_description)}\n}}}}"
            
            for event in quest.events.end:
                if event.type == 'PlayCinematic':
                    quest_template += '\n' + self.get_dialogue(self.cinematictable.get(event.value)) + '\n'
            
            result += quest_template + '\n'
        
        return result

    def get_dialogue(self, scene: 'Scene | None'):
        if scene is None:
            return ''
        
        lines = []
        
        for event in scene.events:
            if event.name != 'CinematicLine':
                continue

            lines.append(
                f"{{{{Dialogue|character={self.path_to_name(event.parameters.get('LineSettings', {}).get('PonyID', ''))}|text={self.loc.translate(event.parameters.get('LineSettings', {}).get('Text_Local', ''))}}}}}"
            )
        
        return '\n'.join(lines)
    
    def path_to_name(self, path: str):
        return PATHS.get(path, path)

            
