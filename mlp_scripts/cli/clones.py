from .cli import CLI, CLICommand



@CLI.register_command
class Clones(CLICommand):
    COMMAND = 'clones'
    HELP = 'Count how many clones and non-clones there are'

    @classmethod
    def build_args(cls, parser):
        parser.add_argument(
            '-i', '--input',
            dest = 'files',
            nargs = '+',
            help = 'Input clones sheets (from https://docs.google.com/spreadsheets/d/1RTkYHWmP7Y8ye2U69f_H4dHs3E0TeHF-edWxPhs-sGA/edit)',
            required = True,
        )

    def run_command(self):
        clones = {}
        for filename in self.args.files:
            clones.update(self.get_table(filename))
        
        print(f'cloned ponies: {len(clones)}')
        print(f'total clones: {sum(len(clone) for clone in clones.values())}')


    def get_table(self, filename: str):
        import csv
        with open(filename, 'r', newline = '') as file:
            reader = csv.reader(file)
            columns = list(zip(*reader))

        clones: dict[str, list[str]] = {}
        current_clone = ''

        for column in columns:
            if column[0]:
                current_clone = column[0]
                continue

            current_clone_list = clones.setdefault(current_clone, [])
            for pony in column:
                if pony and pony:
                    current_clone_list.append(pony)
            
            current_clone_list.pop(0)
        
        return clones
