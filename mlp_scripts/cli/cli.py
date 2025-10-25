import dataclasses
import json
import os
import sys
from abc import abstractmethod
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Type
from ..console import console

@dataclass
class Args(Namespace):
    game_folder: str = ''


class CLI():
    def __init__(self, argv: list[str]) -> None:
        self.argparser = ArgumentParser(
            description = 'Interact with the mlp game api.',
        )
        
        self.build_args()
    
    COMMANDS: 'dict[str, Type[CLICommand]]' = {}
    
    @classmethod
    def register_command(cls, command: 'Type[CLICommand]'):
        if not issubclass(command, CLICommand):
            raise TypeError('action must inherit from CLIAction')
        
        cls.COMMANDS[command.COMMAND] = command
        
        return command
    
    def build_args(self):
        self.argparser.add_argument(
            'game_folder',
            help = 'Game folder'
        )
        
        self.subparser = self.argparser.add_subparsers(
            title = 'commands',
            dest = 'command',
        )
        
        for command in self.COMMANDS.values():
            command.build_args(self.subparser.add_parser(
                command.COMMAND,
                help = command.HELP,
            ))
            
    def parse_args(self, argv: list[str]):
        
        if len(argv) < 1:
            self.argparser.print_help()
            return
        
        args = self.argparser.parse_args(argv, namespace = Args())

        args.game_folder = os.path.abspath(args.game_folder)

        if not os.path.isdir(args.game_folder):
            console.print(f'[red]folder "{args.game_folder}" does not exist')

        command = self.COMMANDS.get(args.command)

        if command is None:
            self.argparser.print_help()
            return
        
        if command:
            command(args).run_command()

class CLICommand():
    COMMAND = ''
    HELP = ''
    args: Args
    
    def __init__(self, args: Args):
        self.args = args
    
    @classmethod
    @abstractmethod
    def build_args(cls, parser: ArgumentParser):
        ...
    
    @abstractmethod
    def run_command(self):
        ...


def register_command(cls):
    CLI.register_command(cls)

    return cls
