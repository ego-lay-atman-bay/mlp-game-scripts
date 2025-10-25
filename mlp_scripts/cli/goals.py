from .cli import CLI, CLICommand

@CLI.register_command
class GoalsCommand(CLICommand):
    COMMAND = 'goals'
    HELP = 'Calculate daily goals stuff'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            'category',
            help = 'Object category to check',
            choices = [
                'pony',
                'shop',
                'decor',
            ],
        )
    
    def run_command(self):
        from luna_kit.typings.defaultGameCampaign import DefaultGameCampaignType
        from luna_kit.gameobjectdata import GameObjectData
        import os
        import json
        from ..console import console
        import math

        CATEGORIES = {
            'pony': 'Pony',
            'shop': 'Pony_House',
            'decor': 'Decore',
        }

        category = CATEGORIES[self.args.category]

        with open(os.path.join(self.args.game_folder, 'defaultGameCampaign.json'), 'r') as file:
            defaultGameCampaign: DefaultGameCampaignType = json.load(file)
        
        gameObjectData = GameObjectData(
            os.path.join(self.args.game_folder, 'gameobjectdata.xml')
        )

        daily_goals = defaultGameCampaign.get('mini_games', {}).get('dailygoals', {}).get('itemshop', [])

        total_cost = 0

        for item in daily_goals:
            obj = gameObjectData.get_object(item['item_id'])
            if obj is None or obj.category != category:
                continue
            
            total_cost += item['cost']
        
        days = math.ceil(total_cost / 120)
        years = days / 365
        
        console.print(f'[yellow]Total cost:[/] {total_cost}')
        console.print(f'[yellow]Days:[/] {days}')
        console.print(f'[yellow]Days:[/] {years:.2f}')

