from Utils.Voice_Assistant import VA
import init


def run():
    init.setup()
    va = VA()
    va.start_VA()


if __name__ == '__main__':
    run()
