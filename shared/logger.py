# logger.py

import sys
import contextvars
import logging
from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from loguru import Record

LEVEL_MAPPING = {
    "DEBUG":    ("dbug", "~~ "),
    "INFO":     ("info", ""),
    "WARNING":  ("warn", "~~ "),
    "ERROR":    ("fail", "!_> "),
    "CRITICAL": ("crit", "### ")
}

TTY_PROMPTS=("^_> ", "~~ ", "!_> ", "### ")

request_id_ctx = contextvars.ContextVar("req_id", default="system")

def set_req_id(req_id: str) -> None:
    request_id_ctx.set(req_id)

# time :: [loglevel] :: [id] :: module :: message
def formatter(record: dict) -> str:
    """
    gets called for every long string
    prepares the data and returns the 'patterned' string
    """

    # get the loguru level name
    lvl_name = record["level"].name

    # get the custom level names and their prefixes
    tty_lvl, auto_prefix = LEVEL_MAPPING.get(lvl_name, (lvl_name.lower()[:4], ""))

    # center custom level names to 4 chars
    record["extra"]["tty_level"] = f"[{tty_lvl:^4}]"

    # get the msg. rule #1: everything in lower case
    msg = record["message"].lower()

    # add a prefix, if not there
    if not msg.startswith(TTY_PROMPTS):
        msg = f"{auto_prefix}{msg}"

    # add our custom msg to extra
    record["extra"]["tty_msg"] = msg

    # if there is no request id, it's a system-important log
    if "req_id" not in record["extra"]:
        record["extra"]["req_id"] = "system"

    # if there's no module's name, just use something
    if "module" not in record["extra"]:
        record["extra"]["module"] = "unkn!!"

    # get the id of THIS, active request
    req_id = request_id_ctx.get()

    # return the string
    return (
        "{time:YYYY-MM-DD HH:mm:ss} :: "
        "{extra[tty_level]} :: "
        f"[#{req_id:<6}] :: "
        "{extra[module]:<8} :: "
        "{extra[tty_msg]}\n"
    )

def setup_logger(module_name: str, log_file: str | None = None):
    """
    initalization function. gets called one time on start
    """

    # remove the default loguru logger
    logger.remove()

    # console output
    logger.add(
            sys.stdout,
            format=formatter,
            level="DEBUG"
    )

    # log file output
    if log_file:
        logger.add(
            log_file,
            format=formatter,
            rotation="10 MB",
            retention="30 days",
            level="INFO"
        )


    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)

    aiogram_logger = logging.getLogger("aiogram")
    aiogram_logger.handlers = [InterceptHandler()]
    aiogram_logger.propagate = False
    aiogram_logger.setLevel(logging.INFO)

    logging.getLogger("httpx").setLevel(logging.WARNING)

    # binding logger with extra["module"]
    return logger.bind(module=module_name)

# copy-paste ai code to achieve style
class InterceptHandler(logging.Handler):
    """
    captures logs from the standart library
    and forwards them to loguru
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            if frame.f_back:
                frame = frame.f_back
            depth += 1

        module_name = record.name.split(".")[0][:7]

        logger.bind(module=module_name).opt(
            depth=depth, exception=record.exc_info
        ).log(level, record.getMessage())
