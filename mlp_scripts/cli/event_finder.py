from .cli import CLI, CLICommand
from typing import Any, Literal

@CLI.register_command
class EventFinderCommand(CLICommand):
    COMMAND = 'event_finder'
    HELP = 'Find events and report their info'
    
    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            'event_files',
            type = str,
            help = 'Event files folder',
        )

        parser.add_argument(
            '-l', '--loc', '--language',
            default = 'english',
            help = 'Loc file to use',
        )

        parser.add_argument(
            '-o', '--output',
            help = 'Output .md file',
            dest = 'output',
        )

        parser.add_argument(
            '-t', '--type',
            choices = 'calendar',
            default = 'calendar',
            dest = 'type',
        )

    def run_command(self):
        import md_generator as md
        import json
        from datetime import datetime
        from luna_kit.gameobjectdata import GameObjectData
        from luna_kit.loc import LOC
        import os
        from ..utils import parse_date


        game_object_data = GameObjectData(
            os.path.join(self.args.game_folder, 'gameobjectdata.xml')
        )


        loc = None

        if os.path.isfile(os.path.join(self.args.game_folder, self.args.loc.lower())):
            loc = LOC(os.path.join(self.args.game_folder, self.args.loc.lower()))
        if os.path.isfile(os.path.join(self.args.game_folder, self.args.loc.lower() + '.loc')):
            loc = LOC(os.path.join(self.args.game_folder, self.args.loc.lower() + '.loc'))
        else:
            raise FileNotFoundError(f'Language {self.args.loc} not found')


        events: dict[str, dict] = {}
        
        for dirpath, dirnames, filenames in os.walk(self.args.event_files):
            for filename in filenames:
                filename: str
                if not filename.endswith('.json'):
                    continue
                try:
                    with open(os.path.join(dirpath, filename), 'r') as file:
                        saved_events: list[dict[str, Any]] = json.load(file)
                    
                    if not isinstance(saved_events, list):
                        continue
                    
                    for event in saved_events:
                        if event.get('owner', {}).get('credential') != 'system:osiris':
                            continue

                        if 'test' in event.get('name', '').lower():
                            continue

                        if event.get('_template', {}).get('event_tuning', {}).get('type', {}).get('value', '') != self.args.type:
                            continue

                        events[event['id']] = event
                except Exception as e:
                    e.add_note(filename)
                    raise e
        

        match self.args.type:
            case 'calendar':
                transformed_event_data: list[dict[Literal['date', 'doc'], datetime | md.Group]] = []

                for event in events.values():
                    doc = md.Paragraph()
                    date = parse_date(event['start_date'])
                    
                    event_data: dict[str, datetime | md.Group] = {
                        'date': date,
                        'doc': doc,
                    }

                    transformed_event_data.append(event_data)

                    doc.append(
                        md.Heading(
                            md.Sentence(
                                date.strftime('%B %Y'),
                                'Calendar'
                            ),
                            level = 2,
                        )
                    )

                    calendar_data: dict = event['_template']['event_tuning']['rewards_data']['value'][0]

                    main_reward_id: str = calendar_data['_cumulative_reward']['reward']
                    main_reward = game_object_data.get_object(main_reward_id)
                    if main_reward is None:
                        raise TypeError(f'Item {main_reward_id} not found')
                    main_reward_name = loc.translate(main_reward.get('Name', {}).get('Unlocal', main_reward_id))
                    doc.append(
                        md.Paragraph(
                            md.Sentence(
                                md.Text('Main Reward:', bold = True),
                                md.Text(main_reward_name),
                                'or',
                                md.Text(calendar_data['_cumulative_reward']['alt_count']),
                                md.Text(calendar_data['_cumulative_reward']['alt_reward']),
                            )
                        )
                    )

                    reward_list = md.List(ordered = True)
                    doc.append(reward_list)

                    if '_days' not in calendar_data:
                        e = KeyError('_days')
                        e.add_note(event['name'])
                        raise e

                    for day in calendar_data['_days']:
                        day: dict

                        reward_id: str = day['reward']
                        reward_name: str = reward_id
                        reward_obj = game_object_data.get_object(reward_id)
                        if reward_obj is not None:
                            if reward_obj.category == 'QuestSpecialItem':
                                seasonal_tokens = {
                                    'Token_Event_Common': 'Common Token',
                                    'Token_Event_Rare': 'Rare Token',
                                }
                                
                                if reward_id in seasonal_tokens:
                                    reward_name = seasonal_tokens[reward_id]
                                else:
                                    reward_name = loc.translate(
                                        reward_obj.get('QuestSpecialItem', {}).get('Name', reward_name)
                                    )
                            else:
                                reward_name = loc.translate(
                                    reward_obj.get('Name', {}).get('Unlocal', reward_name)
                                )

                                match reward_obj.category:
                                    case 'PonyPet':
                                        reward_name += ' (Pet)'
                                    case 'Decore':
                                        reward_name += ' (Decor)'
                                    case 'Pony_House':
                                        reward_name += ' (Shop)'
                                
                        
                        line = md.Sentence()
                        if day['count'] > 1:
                            line.append(day['count'])
                        line.append(reward_name)

                        reward_list.append(line)
                
                transformed_event_data.sort(key = lambda item: item['date'])
                final_doc = md.Group(
                    *(month['doc'] for month in transformed_event_data)
                )

                output = os.path.abspath(self.args.output)
                os.makedirs(os.path.dirname(output), exist_ok = True)
                with open(output, 'w', encoding = 'utf-8') as file:
                    file.write(str(final_doc))
                
                    

                

    
        