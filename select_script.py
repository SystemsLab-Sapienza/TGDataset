import cmd
from language_detection import perform_language_detection
from topic_modeling_LDA import perform_topic_modeling


class TGDatasetShell(cmd.Cmd):

    intro = "Welcome to the TGDataset script explorer! Type help or ? to list commands."
    prompt = '(TGDataset)'
    
    def do_language_detection(self, arg):
        'Starting language detection on the TGDataset'
        perform_language_detection(*parse(arg))

    def do_topic_modeling(self, arg):
        'Starting Topic Modeling on the TGDataset'
        perform_topic_modeling(*parse(arg))
        return True



def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))

if __name__ == '__main__':
    TGDatasetShell().cmdloop()
