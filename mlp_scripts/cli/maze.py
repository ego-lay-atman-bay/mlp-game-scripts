from ..console import console
from .cli import CLI, CLICommand
from dataclasses import dataclass
from typing import Literal

@dataclass
class MazeBlock:
    id: str
    x: int
    y: int
    size: int
    connections: dict[Literal[
        'NorthEast',
        'NorthWest',
        'SouthEast',
        'SouthWest',
    ], bool]
    start: bool = False

@CLI.register_command
class MazeCommand(CLICommand):
    COMMAND = 'maze'
    HELP = 'Get maze info'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            '-o', '--output',
            dest = 'output',
            help = 'Output folder',
            required = True,
        )

    def run_command(self):
        from luna_kit.xml import parse_xml
        from luna_kit.gameobjectdata import GameObjectData
        from luna_kit.utils import strToBool, strToInt
        import os
        from PIL import Image, ImageDraw

        self.game_object_data = GameObjectData(os.path.join(self.args.game_folder, 'gameobjectdata.xml'))
        self.maze_save = parse_xml(os.path.join(self.args.game_folder, 'initial_pony_save_8.xml'))[0][0]

        max_x: int = 0
        max_y: int = 0

        maze: list[MazeBlock] = []
        types: set[str] = set()

        maze_objects = self.maze_save.find('Inital_Objects').find('MazeBlock_Objects')

        for maze_block in maze_objects:
            if maze_block.tag != 'Object':
                continue

            obj_id = maze_block.attrib['ID']

            position_el = maze_block.find('Position')
            maze_obj = self.game_object_data.get_object(obj_id)
            if maze_obj is None or position_el is None:
                console.print(f'Could not find [yellow]{obj_id}[/]')
                continue
            
            entity = maze_block.find('Entity')
            
            block = MazeBlock(
                id = obj_id,
                x = strToInt(position_el.attrib['x']),
                y = strToInt(position_el.attrib['y']),
                size = maze_obj.get('GridData', {}).get('Size', 0),
                connections = {
                    'NorthEast': maze_obj.get('Connections', {}).get('NorthEast', False),
                    'NorthWest': maze_obj.get('Connections', {}).get('NorthWest', False),
                    'SouthEast': maze_obj.get('Connections', {}).get('SouthEast', False),
                    'SouthWest': maze_obj.get('Connections', {}).get('SouthWest', False),
                },
            )

            if entity is not None:
                block.start = entity.get('ID') == 'MazeBlock_Start'
                types.add(entity.attrib['Type'])
            
            max_x = max(max_x, block.x + block.size)
            max_y = max(max_x, block.y + block.size)

            maze.append(block)
            
        maze_image = Image.new('RGBA', (max_x, max_y), (0,0,0,0))
        image_draw = ImageDraw.Draw(maze_image)

        for maze_block in maze:
            image_draw.rectangle(
                (
                    maze_block.x,
                    maze_block.y,
                    maze_block.x + maze_block.size,
                    maze_block.y + maze_block.size,
                ),
                (255, 255, 255, 255) if not maze_block.start else 'yellow',
            )

            top = not maze_block.connections['SouthWest']
            left = not maze_block.connections['SouthEast']
            bottom = not maze_block.connections['NorthEast']
            right = not maze_block.connections['NorthWest']

            if right:
                image_draw.line(
                    (
                        maze_block.x + maze_block.size,
                        maze_block.y,
                        maze_block.x + maze_block.size,
                        maze_block.y + maze_block.size,
                    ),
                    (0,0,0,255),
                    width = 1,
                )
            if top:
                image_draw.line(
                    (
                        maze_block.x,
                        maze_block.y,
                        maze_block.x + maze_block.size,
                        maze_block.y,
                    ),
                    (0,0,0,255),
                    width = 1,
                )
            if bottom:
                image_draw.line(
                    (
                        maze_block.x,
                        maze_block.y + maze_block.size,
                        maze_block.x + maze_block.size,
                        maze_block.y + maze_block.size,
                    ),
                    (0,0,0,255),
                    width = 1,
                )
            if left:
                image_draw.line(
                    (
                        maze_block.x,
                        maze_block.y,
                        maze_block.x,
                        maze_block.y + maze_block.size,
                    ),
                    (0,0,0,255),
                    width = 1,
                )
        
        maze_image = maze_image.rotate(90)

        console.print(types)
        
        output = os.path.abspath(os.path.join(self.args.output, 'maze_image.png'))
        os.makedirs(os.path.dirname(output), exist_ok = True)
        maze_image.save(output)
        console.print(f'Saved to [yellow]{output}[/]')
