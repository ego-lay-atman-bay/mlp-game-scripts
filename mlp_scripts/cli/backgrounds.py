from .cli import CLI, CLICommand

@CLI.register_command
class BackgroundsCommand(CLICommand):
    COMMAND = 'backgrounds'
    HELP = 'Dump backgrounds'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            required = True,
            help = 'Output folder',
        )
    
    def run_command(self):
        from ..console import console
        import os
        from PIL import Image
        from ..crop import crop_image
        from luna_kit.gameobjectdata import GameObjectData
        from luna_kit.loc import LOC


        LOCATIONS = {
            0: 'STR_PONYVILLE',
            1: 'STR_CANTERLOT',
            2: 'STR_SWEET_APPLE_ACRES',
            3: 'STR_EVERFREE_FOREST',
            4: 'STR_CRYSTAL_EMPIRE',
            5: 'STR_CHANGELING_KINGDOM',
            6: 'STR_KLUGETOWN',
        }
        

        loc = LOC(os.path.join(self.args.game_folder, 'english.loc'))
        gameobjectdata = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))

        output = os.path.abspath(self.args.output)
        os.makedirs(output, exist_ok = True)

        for background in gameobjectdata['Theme'].values():
            name = loc.translate(background.get('Appearance', {}).get('Name'))
            if name.isupper():
                name = name.title()
            if name.lower() == 'classic':
                location = LOCATIONS[background.get('Appearance', {}).get('MapZone', 0)]
                name = f'{loc.translate(location).title()} Classic'
            
            console.print(f'saving {name}')

            image = Image.open(os.path.join(
                self.args.game_folder,
                background.get('Appearance', {}).get('Image'),
            ))
            image = crop_image(image)
            
            image.save(os.path.join(output, f'{name} background.png'))


