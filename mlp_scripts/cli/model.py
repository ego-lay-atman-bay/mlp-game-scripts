from .cli import CLI, CLICommand

@CLI.register_command
class ModelCommand(CLICommand):
    COMMAND = 'model'
    HELP = 'Perform stuff on models'

    @classmethod
    def build_args(cls, parser):
        model_command = parser.add_subparsers(
            dest = 'model_command',
        )

        scan = model_command.add_parser(
            'scan',
            help = 'Scan models',
        )

        scan.add_argument(
            '-o', '--output',
            dest = 'output',
            help = 'Output report',
            required = True,
        )
    
    def run_command(self):
        from luna_kit.model.rk import RKModel
        from luna_kit.gameobjectdata import GameObjectData
        import os
        import json

        game_data = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))

        """
        {
            "pony_type01.anim": [
                [
                    'bone'
                ]
            ]
        }
        """

        report: dict[str, list[list[tuple[str, int]]]] = {}

        for pony in game_data['Pony'].values():
            model_name = pony.get('Model', {}).get('MediumLOD')
            anim_name = pony.get('Animation', {}).get('Rig_MediumLOD', '')

            if not model_name:
                continue

            rk = RKModel(os.path.join(self.args.game_folder, f'{model_name}.rk'))

            bones = [(bone.name, bone.parentIndex) for bone in rk.bones]

            if bones not in report.setdefault(anim_name, []):
                report[anim_name].append(bones)
        
        with open(self.args.output, 'w', encoding = 'utf-8') as file:
            json.dump(report, file, indent = 2, ensure_ascii = False)
