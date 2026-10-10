from .cli import CLI, CLICommand
from ..console import console
from typing import TypedDict

class NormalizedFortuneShopItem(TypedDict):
    id: str
    category: str
    name: str
    amount: int
    prices: dict[str, int]
    royal: dict[str, int]
    

@CLI.register_command
class FortuneShopCommand(CLICommand):
    COMMAND = 'fortune_shop'
    HELP = 'Create fortune shop table'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            '-i', '--input',
            dest = 'input',
            help = 'Fortune shop .json data',
        )

        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            help = 'Output folder for csv files',
            required = False,
        )
    
    def run_command(self):
        from luna_kit.typings.defaultGameCampaign import DefaultGameCampaignType, FortuneShopDataType
        from luna_kit.loc import LOC
        from luna_kit.gameobjectdata import GameObjectData
        import os
        import json
        from pathlib import Path
        import csv

        fortune_shop: FortuneShopDataType | None = None

        if self.args.input is None:
            with open(os.path.join(self.args.game_folder, 'defaultGameCampaign.json'), 'r') as file:
                defaultGameCampaign: DefaultGameCampaignType = json.load(file)
            
            fortune_shop = defaultGameCampaign['global_defines'].get('fortune_shop_data', defaultGameCampaign['global_defines'].get('personal_shop_data'))
        elif os.path.exists(self.args.input):
            with open(self.args.input, 'r') as file:
                fortune_shop = json.load(file)
        
        if fortune_shop is None:
            raise FileNotFoundError(f'Cannot find fortune shop data "{self.args.input}"')
        
        game_object_data = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))
        loc = LOC(os.path.join(self.args.game_folder, 'english.loc'))
        
        normalized_lists: dict[str, list[NormalizedFortuneShopItem]] = {}

        sale_types = list(
            fortune_shop.get(
                'item_price_chances',
                fortune_shop.get(
                    'item_discount_chances',
                    {}
                ),
            ).keys()
        )

        for list_name, item_list in fortune_shop.get('item_lists', {}).items():
            for item in item_list:
                normalized_item: NormalizedFortuneShopItem = {
                    'id': item['id'],
                    'category': '',
                    'name': item['id'],
                    'amount': item.get('amount', 1),
                    'prices': {},
                    'royal': {},
                }

                game_object = game_object_data.get_object(item['id'])
                if game_object is None:
                    console.print(f'[yellow]{item['id']}[/yellow] not found')
                    continue
                
                normalized_item['category'] = game_object.category

                match game_object.category:
                    case 'QuestSpecialItem':
                        name_id = game_object.get('QuestSpecialItem', {}).get('Name')
                    case 'ProfileAvatar' | 'ProfileAvatarFrame' | 'PlayerCardBackground' | "PlayerCardBackgroundFrame" | 'PlayerCardCutieMark':
                        name_id = item['id']
                    case 'ProgressBooster':
                        name_id = game_object.get('Shop', {}).get('Label')
                    case _:
                        name_id = game_object.get('Name', {}).get('Unlocal')
                    
                name = loc.translate(name_id or item['id'])

                normalized_item['name'] = name

                for i, type in enumerate(sale_types):
                    normalized_item['prices'][type] = item['price_list'][i]
                    if 'sub_price_list' in item:
                        normalized_item['royal'][type] = item['sub_price_list'][i]
                
                normalized_lists.setdefault(list_name, []).append(normalized_item)
        
        output_folder = Path(self.args.output)
        output_folder.mkdir(exist_ok = True, parents = True)
        
        names: list[str] = []
        for list_name, item_list in normalized_lists.items():
            show_amount = set[str]()
            show_royal_base = set[str]()

            table: list[dict] = []
            categories: dict[str, list[dict]] = {}

            for item in item_list:
                row = {
                    'category': item['category'],
                    'name': item['name'],
                    'amount': item['amount'],
                }

                for sale_type, price in item['prices'].items():
                    row[sale_type] = price

                for sale_type, price in item['royal'].items():
                    row[f'royal {sale_type}'] = price
                
                if item['prices']['regular'] != item['royal'].get('regular'):
                    show_royal_base.add(item['category'])
                    console.print(f'{item['id']} has different roayal base price')
                
                if item['amount'] > 1:
                    show_amount.add(item['category'])

                if item['name'] not in names:
                    names.append(item['name'])
                else:
                    console.print(f'Duplcated name: {item['name']}')
                
                table.append(row)
                categories.setdefault(item['category'], []).append(row)
            
            fieldnames = ['name']
            if len(show_amount):
                fieldnames.append('amount')
            fieldnames.extend(sale_types)
            for sale_type in sale_types:
                if sale_type == 'regular' and not len(show_royal_base):
                    continue
                fieldnames.append(f'royal {sale_type}')
            
            console.print(f'Writing [green]{list_name}.csv[/green]')
            with open(output_folder/f'{list_name}.csv', 'w', newline = '') as file:
                writer = csv.DictWriter(file, fieldnames, extrasaction = 'ignore')
                writer.writeheader()
                writer.writerows(table)
            
            wikitext = ''

            for category, table in categories.items():
                fieldnames = ['name']
                if category in show_amount:
                    fieldnames.append('amount')
                fieldnames.extend(sale_types)
                for sale_type in sale_types:
                    if sale_type == 'regular' and category not in show_royal_base:
                        continue
                    fieldnames.append(f'royal {sale_type}')
                
                wikitext += f'== {category} ==\n\n'

                wikitext += '{| class="sortable article-table mw-collapsible"\n'
                wikitext += '|-\n'
                for field in fieldnames:
                    if field == 'name':
                        field = 'Item'
                    
                    field = field.title()
                    wikitext += f'! {field}\n'
                
                for row in table:
                    wikitext += '|-\n'
                    for field in fieldnames:
                        value = row[field]
                        if field == 'name':
                            if row['category'] in ['Pony', 'Pony_House']:
                                value = f'[[{value}]]'
                            elif row['category'] in ['ProfileAvatar', 'ProfileAvatarFrame', 'PlayerCardBackground', "PlayerCardBackgroundFrame", 'PlayerCardCutieMark']:
                                value = f'[[File:{value}.png]]'
                        wikitext += f'| {value}\n'
                
                wikitext += '|}\n\n'

            console.print(f'Writing [green]{list_name}.wikitext[/green]')
            with open(output_folder/f'{list_name}.wikitext', 'w', encoding = 'utf-8') as file:
                file.write(wikitext)

