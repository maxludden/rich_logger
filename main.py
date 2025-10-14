""" main.py"""
from rich_loguru import log

def main() -> None:
    '''Main function to demonstrate logging.'''
    log.trace("Trace message")
    log.info("Hello, colourful world!")
    log.success("All systems go")

if __name__ == "__main__":
    main()
