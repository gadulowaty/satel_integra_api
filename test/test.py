import asyncio
import logging
import os.path
import sys
import secure

import satel_integra_api as integra_api
from colorlog import ColoredFormatter

from asyncio.events import AbstractEventLoop

from satel_integra_api import IntegraSystem, IntegraItem, IntegraStateEvent, IntegraClientStatus
from satel_integra_api.objects import IntegraStateBase
from satel_integra_api.base import IntegraTypeVal

# FORMAT = "[%(thread)d][%(taskName)s][%(filename)s:%(lineno)s][%(levelname)s]: %(message)s"
FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s (%(taskName)s) [%(name)s:%(lineno)s] %(message)s"
FORMAT_DATE: str = "%Y-%m-%d"
FORMAT_TIME: str = "%H:%M:%S"
FORMAT_DATETIME: str = f"{FORMAT_DATE} {FORMAT_TIME}"

def sys_logging_configure( loglevel=logging.INFO ):
    colorfmt = f"%(log_color)s{FORMAT}%(reset)s"
    logging.basicConfig( level=loglevel, stream=sys.stdout )
    logger = logging.getLogger()
    logger.handlers[ 0 ].setFormatter(
        ColoredFormatter(
            colorfmt,
            datefmt=FORMAT_DATETIME,
            reset=True,
            log_colors={
                "DEBUG": "light_black",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        )
    )
    logging.basicConfig( format=FORMAT, datefmt=FORMAT_DATETIME, level=loglevel )

sys_logging_configure( logging.DEBUG )

_LOGGER = logging.getLogger( __name__ )


async def sys_event_handler( event_name: str, sender: IntegraSystem, state: IntegraStateBase, previous: IntegraTypeVal, **kwargs ) -> None:
    _LOGGER.debug( f"{event_name}: {state}, from {previous} to {state.value}" )
    return None


async def sys_item_event_handler( event_name: str, sender: IntegraSystem, item: IntegraItem, state: IntegraStateEvent, **kwargs ) -> None:
    _LOGGER.debug( f"{event_name}: from {sender.__class__.__name__}::{item.__class__.__name__}::{item.id_str}:'{item.name}' => {state}" )
    return None


async def sys_client_event_handler( event_name: str, sender: IntegraSystem, event: integra_api.IntegraClientStatus, **kwargs ) -> None:
    _LOGGER.debug( f'Received event: {event_name} from {sender} => {event.name}' )
    if event == integra_api.IntegraClientStatus.CONNECTED:
        _LOGGER.info( f"{sender.client.integra_version}" )
        _LOGGER.info( f"{sender.client.module_version}" )
        _LOGGER.info( f"{sender.caps}" )

    return None


async def async_main( eventloop: AbstractEventLoop | None ):

    if eventloop is None:
        eventloop = asyncio.get_running_loop()

    asyncio.current_task().set_name( f"async_main" )

    async def load_progress( current: int, total: int ) -> bool:
        _LOGGER.debug( f"load_progress: got {current} of {total}" )
        return True

    system = integra_api.IntegraSystem.tcp( secure.TEST_HOST_IP, 7094, eventloop, secure.client_opts )
    system.subscribe( integra_api.Events.EVENT_SYS_EVENT, sys_event_handler )
    system.subscribe( integra_api.Events.EVENT_SYS_CLIENT_EVENT, sys_client_event_handler )
    system.subscribe( integra_api.Events.EVENT_SYS_ITEM_CHANGED, sys_item_event_handler )

    try:
        if not await system.async_connect( retries=5 ):
            return

        await system.async_monitor_start( integra_api.IntegraAllNotifyEvents )

        cache_file = os.path.join( os.path.dirname( __file__ ), "system.json" )
        system.system_info_load( cache_file )

        user_self = await system.client.async_user_read_self()
        if user_self is not None:
            _LOGGER.info( f"Welcome back, {user_self.name}..." )

        system_loaded = await system.async_system_info_wait_for( load_progress )
        _LOGGER.info( f"System loaded: {system_loaded}" )

        with system.monitor_configure():
            system.outputs[ 23 ].power_monitor = 5
            system.zones[ 21 ].temp_monitor = system.zones[ 41 ].temp_monitor = system.zones[ 42 ].temp_monitor = 10

        index = 0
        while system.status != IntegraClientStatus.DISCONNECTED:
            index += 1
            _LOGGER.debug( f"Running-{index}: ({system.status.name})" )
            await asyncio.sleep( 5 )
            if index >= 3:
                break

        _LOGGER.debug( f"Finishing: {system.status.name}" )


    except Exception as err:
        _LOGGER.error( err )

    finally:
        _LOGGER.debug( "Finalizing: ..." )
        await system.async_disconnect()


def main():
    asyncio.run(async_main( None ))
    _LOGGER.info( "Going home for good..." )


if __name__ == "__main__":
    main()
