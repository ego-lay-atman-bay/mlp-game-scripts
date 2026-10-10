from .cli import CLI, CLICommand

@CLI.register_command
class PonyListCommand(CLICommand):
    COMMAND = 'pony_list'
    HELP = 'Generate a list of ponies'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            'start',
            help = 'Start pony',
        )

        parser.add_argument(
            'end',
            help = 'End pony',
        )

        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            help = 'Output file',
            required = True,
        )

    def run_command(self):
        from luna_kit.gameobjectdata import GameObjectData
        from luna_kit.loc import LOC
        import os
        import md_generator as md


        gameobjectdata = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))
        locale = LOC(os.path.join(self.args.game_folder, 'english.loc'))

        pony_ids = list(gameobjectdata['Pony'].keys())

        start_index = pony_ids.index(self.args.start)
        end_index = pony_ids.index(self.args.end)

        table = []

        for index in range(start_index, end_index + 1):
            pony_id = pony_ids[index]
            pony = gameobjectdata['Pony'].get(pony_id)
            if pony is None:
                continue

            table.append([
                '[ ]',
                pony_id,
                pony.get('Model', {}).get('MediumLOD'),
                locale.translate(pony.get('Name', {}).get('Unlocal', pony_id))
            ])

        md_table = md.Table(
            ['done', 'id', 'model', 'name'],
            table,
            [md.enums.ALIGNMENT.RIGHT, md.enums.ALIGNMENT.LEFT, md.enums.ALIGNMENT.LEFT, md.enums.ALIGNMENT.LEFT]
        )

        output = os.path.abspath(self.args.output)
        os.makedirs(os.path.dirname(output), exist_ok = True)
        with open(output, 'w') as file:
            file.write(str(md_table))
        
        print(f'saved to "{output}"')
