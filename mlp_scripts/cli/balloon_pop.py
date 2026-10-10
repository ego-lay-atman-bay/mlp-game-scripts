from .cli import CLI, CLICommand
from typing import Literal
from ..console import console

@CLI.register_command
class BalloonPopCommand(CLICommand):
    COMMAND = 'balloon_pop'
    HELP = "Calculate chances for balloon pop"

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            'lottery',
            help = 'Lottery (balloon pop) to get',
        )

        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            help = 'Output csv file',
            required = True,
        )

    def run_command(self):
        import json
        import os
        import csv
        from luna_kit.typings.defaultGameCampaign import DefaultGameCampaignType
        
        console.print('loading defaultGameCampaign.json')
        with open(os.path.join(self.args.game_folder, 'defaultGameCampaign.json'), 'r') as file:
            defaultGameCampaign: DefaultGameCampaignType = json.load(file)

        loot_table = defaultGameCampaign.get('mini_games', {}).get('balloonpop', {}).get('lottos_list', {})[self.args.lottery].get('loot_table', [])
        table: list[dict[Literal['id', 'chance', 'min', 'max'], str | float | int]] = []

        total_weight = sum(loot.get('weight', 0) for loot in loot_table)
        
        console.print('calculating chances')
        for loot in loot_table:
            table.append({
                'id': loot.get('type_name', ''),
                'chance': (loot.get('weight', 0) / total_weight) * 100,
                'min': loot.get('min', 0),
                'max': loot.get('max', 0),
            })

        output = os.path.abspath(self.args.output)
        os.makedirs(os.path.dirname(output), exist_ok = True)
        
        with open(output, 'w', newline = '') as file:
            csvwriter = csv.DictWriter(file, ['id', 'chance', 'min', 'max'])
            csvwriter.writeheader()
            csvwriter.writerows(table)
        
        console.print(f'saved to [green]{output}[/]')
