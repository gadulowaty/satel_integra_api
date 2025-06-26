import asyncio
import logging
import queue
import traceback

from asyncio import CancelledError as AsyncCancelledError
from typing import Any, Callable, Awaitable, Union
from enum import IntEnum, StrEnum, Flag

_LOGGER = logging.getLogger( __name__ )

IntegraTypeVal = Union[ int, str, bool, float, IntEnum, StrEnum, Flag ]


class IntegraDoW( IntEnum ):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class IntegraBaseType( IntEnum ):
    INTEGRA_24 = 0
    INTEGRA_32 = 1
    INTEGRA_64_64PLUS = 2
    INTEGRA_128_128PLUS = 3
    INTEGRA_128_WRL = 4
    INTEGRA_256PLUS = 8
    INTEGRA_UNKNOWN = 255


IntegraBaseTypes = set( item.value for item in IntegraBaseType )


class IntegraType( IntEnum ):
    INTEGRA_24 = 0
    INTEGRA_32 = 1
    INTEGRA_64 = 2
    INTEGRA_128 = 3
    INTEGRA_128_WRL_SIM300 = 4
    INTEGRA_64_PLUS = 66
    INTEGRA_128_PLUS = 67
    INTEGRA_256_PLUS = 68
    INTEGRA_128_WRL_LEON = 132
    INTEGRA_UNKNOWN = 255


IntegraTypes = set( item.value for item in IntegraType )


class IntegraTypeName( StrEnum ):
    INTEGRA_24 = "Satel Integra 24"
    INTEGRA_32 = "Satel Integra 32"
    INTEGRA_64 = "Satel Integra 64"
    INTEGRA_128 = "Satel Integra 128"
    INTEGRA_128_WRL_SIM300 = "Satel Integra 128 WRL SIM300"
    INTEGRA_64_PLUS = "Satel Integra 64 Plus"
    INTEGRA_128_PLUS = "Satel Integra 128 Plus"
    INTEGRA_256_PLUS = "Satel Integra 256 Plus"
    INTEGRA_128_WRL_LEON = "Satel Integra 128 WRL LEON"
    INTEGRA_UNKNOWN = "Unknown"


class IntegraModuleCaps( Flag ):
    MODULE_CAP_EMPTY = 0
    MODULE_CAP_32BYTE = 1
    MODULE_CAP_TROUBLE8 = 2
    MODULE_CAP_ARM_NO_BYPASS = 4


class IntegraArmMode( IntEnum ):
    MODE_0 = 0
    MODE_1 = 1
    MODE_2 = 2
    MODE_3 = 3


class IntegraTroubles( IntEnum ):
    BLOCK_1 = 1
    BLOCK_2 = 2
    BLOCK_3 = 3
    BLOCK_4 = 4
    BLOCK_5 = 5
    BLOCK_6 = 6
    BLOCK_7 = 7
    BLOCK_8 = 8


class Integra1stCodeAction( IntEnum ):
    ARMING = 0
    DISARMING = 1
    CANCELING = 2


class IntegraLang( IntEnum ):
    PL = 0
    EN = 1
    UA = 2
    RU = 3
    DE = 4
    SK = 5
    IT = 6
    CZ = 7
    HU = 8
    NL = 9
    IE = 10
    NO = 11
    DK = 12
    IS = 13
    GR = 14
    FR = 15
    ES = 16
    PT = 17
    FI = 18
    SI = 19
    SE = 20
    TR = 21
    RO = 22
    EE = 23
    BG = 24
    LV = 25
    MK = 26
    RS = 27
    AL = 28
    AU = 29
    LT = 30
    UN = 255


IntegraLangs = set( item.value for item in IntegraLang )


class IntegraDispatcher:
    _instance_cnt: int = 0

    def __init__( self, instance_id: int, process_fn: Callable[ ..., Awaitable[ None ] ] ) -> None:
        super().__init__()
        self._instance_id = instance_id
        self._name = f"event_queue_task-{self._instance_id}"
        self._lock: asyncio.Lock = asyncio.Lock()
        self._event: asyncio.Event = asyncio.Event()
        self._queue: queue.Queue = queue.Queue()
        self._process_fn: Callable[ ..., Awaitable[ None ] ] = process_fn
        self._task = asyncio.create_task( self._dispatcher_task(), name=self._name )

    async def _dispatcher_task( self ) -> None:

        _LOGGER.debug( f"[{self._name}] task start" )
        task_self = asyncio.current_task()
        # noinspection PyBroadException
        try:
            while self._queue is not None and task_self.cancelling() == 0:
                if await self._event.wait():
                    event_item = await self._get()
                    if event_item is not None:
                        # noinspection PyBroadException
                        try:
                            await self._process_fn( **event_item )
                        except Exception as err:
                            _LOGGER.error( f"[{self._name}] {traceback.format_exc()}" )
                            _LOGGER.error( f"[{self._name}] task process exception, {err}" )
                            continue

        except AsyncCancelledError:
            # _LOGGER.warning( f"[{self._name}]: CANCELLED" )
            pass

        except Exception as err:
            self._task = None
            _LOGGER.error( f"[{self._name}]: ERROR, {err}" )

        finally:
            event_queue = self._queue
            self._queue = None
            self._flush( event_queue )
            self._task = None
            _LOGGER.debug( f"[{self._name}]: FINISHED {'(Cancelled)' if task_self.cancelling() != 0 else ''}" )

        return None

    @staticmethod
    def _flush( event_queue: queue.Queue ) -> None:
        while True:
            try:
                event_queue.get( False )
            except queue.Empty:
                break
        return None

    async def _get( self ) -> dict[ str, Any ] | None:

        result = None
        async with self._lock:
            try:
                if self._queue is not None:
                    result = self._queue.get( False )
            except queue.Empty:
                self._event.clear()
                return None

        return result

    async def put( self, **kwargs ) -> None:
        async with self._lock:
            if self._queue is not None:
                self._queue.put( kwargs )
                self._event.set()
            else:
                _LOGGER.error( f"[{self._name}] queue not found, discarding" )

    async def shutdown( self, owner: object = None, attr_name: str = None ) -> None:
        if owner is not None and str is not None and hasattr( owner, attr_name ):
            setattr( owner, attr_name, None )

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except Exception as err:
                _LOGGER.debug( f"[{self._name}] awaiting for task finished with {err}")
            self._task = None
        return

    @classmethod
    def create( cls, process_fn: Callable[ ..., Awaitable[ None ] ] ) -> 'IntegraDispatcher':
        result = IntegraDispatcher( cls._instance_cnt, process_fn )
        cls._instance_cnt += 1
        return result


class IntegraEntity( object ):

    def __str__( self ):
        fields_str = ""
        fields = { }
        self._write_fields( fields )
        if len( fields ):
            for name, value in fields.items():
                fields_str += f"{name}={value}; "
            fields_str = f" {fields_str.rstrip( "; " )} "
        return f"{self.__class__.__name__}[{fields_str}]"

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        pass

    def __init__( self ):
        super().__init__()


class IntegraError( Exception ):

    def __str__(self) -> str:
        return self.message

    def __init__( self ):
        super().__init__()

    @property
    def message(self) -> str:
        raise NotImplementedError()

class IntegraRequestError( IntegraError ):

    def __init__( self, message: str = "" ):
        super().__init__(  )
        self._message = message

    @property
    def message(self) -> str:
        return f"{self._message if self._message else self.__class__.__name__}"

IntegraContextRefCntCommitCallback = Callable[ [ ], None ]


class IntegraContextRefCnt( IntegraEntity ):

    def __enter__( self ):
        self._ref_count += 1

    def __exit__( self, exc_type, exc_val, exc_tb ):
        self._ref_count -= 1
        if self._ref_count == 0:
            if self._commit_callback is not None and self._changed:
                self._commit_callback()
            self._changed = False

    def __init__( self, commit_callback: IntegraContextRefCntCommitCallback | None ):
        super().__init__()
        self._ref_count = 0
        self._commit_callback: IntegraContextRefCntCommitCallback = commit_callback
        self._changed: bool = False

    @property
    def changed( self ) -> bool:
        return self._changed

    @changed.setter
    def changed( self, value ):
        self._changed = value

    @property
    def ref_count( self ) -> int:
        return self._ref_count


class IntegraCaps:

    def __str__( self ):
        return f"{self.__class__.__name__}[ Type={self.integra_type.name}; Partitions={self.parts}; Zones={self.zones}; Outputs={self.outputs}; Timers={self.timers}; " \
               f"MCount={self.manipulators}; ECount={self.expanders}; MBus={self.manipulator_buses}; EBus={self.expander_buses}; " \
               f"Users={self.users}; Admins={self.admins}; Masking={self.masking} ]"

    def __init__( self, integra_type: IntegraType, objects: int, parts: int, zones: int, outputs: int, timers: int, phones: int,
                  manipulators: int, expanders: int,
                  manipulator_buses: int, expander_buses: int,
                  users: int, admins: int,
                  masking: bool ) -> None:
        self._integra_type = integra_type
        self._objects = objects
        self._parts = parts
        self._zones = zones
        self._outputs = outputs
        self._timers = timers
        self._phones = phones
        self._manipulators = manipulators
        self._expanders = expanders
        self._manipulator_buses = manipulator_buses
        self._expander_buses = expander_buses
        self._users = users
        self._admins = admins
        self._masking = masking

    @property
    def integra_type( self ) -> IntegraType:
        return self._integra_type

    @property
    def objects( self ) -> int:
        return self._objects

    @property
    def parts( self ) -> int:
        return self._parts

    @property
    def zones( self ) -> int:
        return self._zones

    @property
    def outputs( self ) -> int:
        return self._outputs

    @property
    def timers( self ) -> int:
        return self._timers

    @property
    def doors( self ) -> int:
        return self._expanders

    @property
    def phones( self ) -> int:
        return self._phones

    @property
    def manipulators( self ) -> int:
        return self._manipulators

    @property
    def expanders( self ) -> int:
        return self._expanders

    @property
    def manipulator_buses( self ) -> int:
        return self._manipulator_buses

    @property
    def expander_buses( self ) -> int:
        return self._expander_buses

    @property
    def users( self ) -> int:
        return self._users

    @property
    def admins( self ) -> int:
        return self._admins

    @property
    def masking( self ) -> bool:
        return self._masking


class IntegraMap:
    __MAP_TYPE_TO_NAME: dict[ IntegraType, IntegraTypeName ] = {
        IntegraType.INTEGRA_24: IntegraTypeName.INTEGRA_24,
        IntegraType.INTEGRA_32: IntegraTypeName.INTEGRA_32,
        IntegraType.INTEGRA_64: IntegraTypeName.INTEGRA_64,
        IntegraType.INTEGRA_128: IntegraTypeName.INTEGRA_128,
        IntegraType.INTEGRA_128_WRL_SIM300: IntegraTypeName.INTEGRA_128_WRL_SIM300,
        IntegraType.INTEGRA_64_PLUS: IntegraTypeName.INTEGRA_64_PLUS,
        IntegraType.INTEGRA_128_PLUS: IntegraTypeName.INTEGRA_128,
        IntegraType.INTEGRA_256_PLUS: IntegraTypeName.INTEGRA_256_PLUS,
        IntegraType.INTEGRA_128_WRL_LEON: IntegraTypeName.INTEGRA_128_WRL_LEON,
        IntegraType.INTEGRA_UNKNOWN: IntegraTypeName.INTEGRA_UNKNOWN
    }
    __MAP_NAME_TO_TYPE: dict[ IntegraTypeName, IntegraType ] = {
        v: k for k, v in __MAP_TYPE_TO_NAME.items()
    }
    __MAP_INTEGRA_TYPE_TO_CAPS: dict[ IntegraType, IntegraCaps ] = {
        IntegraType.INTEGRA_24: IntegraCaps( IntegraType.INTEGRA_24,
                                             1, 4, 24, 24, 16, 16,
                                             4, 32, 1, 1,
                                             16, 1, False ),
        IntegraType.INTEGRA_32: IntegraCaps( IntegraType.INTEGRA_32,
                                             4, 16, 32, 32, 28, 16,
                                             4, 32, 1, 1,
                                             64, 4, False ),
        IntegraType.INTEGRA_64: IntegraCaps( IntegraType.INTEGRA_64,
                                             8, 32, 64, 64, 64, 16,
                                             8, 64, 1, 2,
                                             192, 8, False ),
        IntegraType.INTEGRA_64_PLUS: IntegraCaps( IntegraType.INTEGRA_64_PLUS, 8, 32, 64, 64, 64, 16,
                                                  8, 64, 1, 2,
                                                  192, 8, True ),
        IntegraType.INTEGRA_128: IntegraCaps( IntegraType.INTEGRA_128, 8, 32, 128, 128, 64, 16,
                                              8, 64, 1, 2,
                                              240, 8, False ),
        IntegraType.INTEGRA_128_PLUS: IntegraCaps( IntegraType.INTEGRA_128_PLUS, 8, 32, 128, 128, 64, 16,
                                                   8, 64, 1, 2,
                                                   240, 8, True ),
        IntegraType.INTEGRA_128_WRL_LEON: IntegraCaps( IntegraType.INTEGRA_128_WRL_LEON, 8, 32, 128, 128, 64, 16,
                                                       8, 32, 1, 1,
                                                       240, 8, False ),
        IntegraType.INTEGRA_128_WRL_SIM300: IntegraCaps( IntegraType.INTEGRA_128_WRL_SIM300, 8, 32, 128, 128, 64, 16,
                                                         8, 32, 1, 1,
                                                         240, 8, False ),
        IntegraType.INTEGRA_256_PLUS: IntegraCaps( IntegraType.INTEGRA_256_PLUS, 8, 32, 256, 256, 64, 16,
                                                   8, 64, 1, 2,
                                                   240, 8, True ),
        IntegraType.INTEGRA_UNKNOWN: IntegraCaps( IntegraType.INTEGRA_UNKNOWN, 0, 0, 0, 0, 0, 0,
                                                  0, 0, 0, 0,
                                                  0, 0, False ),
    }

    @classmethod
    def type_to_caps( cls, integra_type: IntegraType ) -> IntegraCaps:
        if integra_type in cls.__MAP_INTEGRA_TYPE_TO_CAPS:
            return cls.__MAP_INTEGRA_TYPE_TO_CAPS[ integra_type ]
        return cls.__MAP_INTEGRA_TYPE_TO_CAPS[ IntegraType.INTEGRA_UNKNOWN ]

    @classmethod
    def type_to_name( cls, integra_type: IntegraType ) -> str:
        if integra_type in cls.__MAP_TYPE_TO_NAME:
            return cls.__MAP_TYPE_TO_NAME.get( integra_type )
        return IntegraTypeName.INTEGRA_UNKNOWN

    @classmethod
    def name_to_type( cls, integra_name: IntegraTypeName ) -> IntegraType:
        if integra_name in cls.__MAP_NAME_TO_TYPE:
            return cls.__MAP_NAME_TO_TYPE.get( integra_name )
        return IntegraType.INTEGRA_UNKNOWN
