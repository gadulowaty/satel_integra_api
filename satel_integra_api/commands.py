import logging
import sys

from datetime import datetime
from enum import IntEnum, Flag
from typing import TypeVar

from .base import IntegraDoW, IntegraBaseType, IntegraBaseTypes, Integra1stCodeAction, IntegraLang, IntegraLangs, IntegraType, IntegraTypes, IntegraModuleCaps
from .data import IntegraBuffer, IntegraEntityData
from .elements import IntegraElementType, IntegraElement, IntegraExpanderElement, IntegraManipulatorElement, IntegraAdminElement
from .tools import IntegraHelper
from .users import IntegraUser, IntegraUserDeviceMgmtFunc, IntegraUserDeviceMgmtFuncs, IntegraUserDevice, IntegraUserLocks

_LOGGER = logging.getLogger( __name__ )


class IntegraCommand( IntEnum ):
    READ_ZONES_VIOLATION = 0x00
    READ_ZONES_TAMPER = 0x01
    READ_ZONES_ALARM = 0x02
    READ_ZONES_TAMPER_ALARM = 0x03
    READ_ZONES_ALARM_MEMORY = 0x04
    READ_ZONES_TAMPER_ALARM_MEMORY = 0x05
    READ_ZONES_BYPASS = 0x06
    READ_ZONES_NO_VIOLATION_TROUBLE = 0x07
    READ_ZONES_LONG_VIOLATION_TROUBLE = 0x08
    READ_PARTS_ARMED_SUPPRESSED = 0x09
    READ_PARTS_ARMED_REALLY = 0x0A
    READ_PARTS_ARMED_MODE_2 = 0x0B
    READ_PARTS_ARMED_MODE_3 = 0x0C
    READ_PARTS_1ST_CODE_ENTERED = 0x0D
    READ_PARTS_ENTRY_TIME = 0x0E
    READ_PARTS_EXIT_TIME_ABOVE_10 = 0x0F
    READ_PARTS_EXIT_TIME_BELOW_10 = 0x10
    READ_PARTS_TEMP_BLOCKED = 0x11
    READ_PARTS_BLOCKED_FOR_GUARD = 0x12
    READ_PARTS_ALARM = 0x13
    READ_PARTS_FIRE_ALARM = 0x14
    READ_PARTS_ALARM_MEMORY = 0x15
    READ_PARTS_FIRE_ALARM_MEMORY = 0x16
    READ_OUTPUTS_STATE = 0x17
    READ_DOORS_OPENED = 0x18
    READ_DOORS_OPENED_LONG = 0x19
    READ_RTC_AND_STATUS = 0x1A
    READ_TROUBLES_PART1 = 0x1B
    READ_TROUBLES_PART2 = 0x1C
    READ_TROUBLES_PART3 = 0x1D
    READ_TROUBLES_PART4 = 0x1E
    READ_TROUBLES_PART5 = 0x1F
    READ_TROUBLES_MEMORY_PART1 = 0x20
    READ_TROUBLES_MEMORY_PART2 = 0x21
    READ_TROUBLES_MEMORY_PART3 = 0x22
    READ_TROUBLES_MEMORY_PART4 = 0x23
    READ_TROUBLES_MEMORY_PART5 = 0x24
    READ_PARTS_WITH_VIOLATED_ZONES = 0x25
    READ_ZONES_ISOLATE = 0x26
    READ_PARTS_WITH_VERIFIED_ALARMS = 0x27
    READ_ZONES_MASKED = 0x28
    READ_ZONES_MASKED_MEMORY = 0x29
    READ_PARTS_ARMED_MODE_1 = 0x2A
    READ_PARTS_WITH_WARNING_ALARMS = 0x2B
    READ_TROUBLES_PART6 = 0x2C
    READ_TROUBLES_PART7 = 0x2D
    READ_TROUBLES_MEMORY_PART6 = 0x2E
    READ_TROUBLES_MEMORY_PART7 = 0x2F
    READ_TROUBLES_PART8 = 0x30
    READ_TROUBLES_MEMORY_PART8 = 0x31

    READ_OUTPUT_POWER = 0x7B
    READ_MODULE_VERSION = 0x7C
    READ_ZONE_TEMPERATURE = 0x7D
    READ_INTEGRA_VERSION = 0x7E
    READ_SYSTEM_CHANGES = 0x7F

    EXEC_ARM_MODE_0 = 0x80
    EXEC_ARM_MODE_1 = 0x81
    EXEC_ARM_MODE_2 = 0x82
    EXEC_ARM_MODE_3 = 0x83
    EXEC_DISARM = 0x84
    EXEC_CLEAR_ALARM = 0x85
    EXEC_FORCE_ARM_MODE_0 = 0xA0
    EXEC_FORCE_ARM_MODE_1 = 0xA1
    EXEC_FORCE_ARM_MODE_2 = 0xA2
    EXEC_FORCE_ARM_MODE_3 = 0xA3
    EXEC_ZONES_BYPASS_SET = 0x86
    EXEC_ZONES_BYPASS_UNSET = 0x87
    EXEC_OUTPUTS_ON = 0x88
    EXEC_OUTPUTS_OFF = 0x89
    EXEC_OPEN_DOOR = 0x8A
    EXEC_CLEAR_TROUBLE_MEMORY = 0x8B
    EXEC_READ_EVENT = 0x8C
    EXEC_ENTER_1ST_CODE = 0x8D
    EXEC_SET_RTC_CLOCK = 0x8E
    EXEC_GET_EVENT_TEXT = 0x8F
    EXEC_ZONES_ISOLATE = 0x90
    EXEC_OUTPUTS_SWITCH = 0x91

    USER_READ_SELF_INFO = 0xE0
    USER_READ_OTHER_INFO = 0xE1
    USER_READ_USERS_LIST = 0xE2
    USER_READ_USER_LOCKS = 0xE3
    USER_WRITE_USER_LOCKS = 0xE4
    USER_REMOVE = 0xE5
    USER_CREATE = 0xE6
    USER_CHANGE = 0xE7
    USER_MANAGE_DEVS = 0xE8
    USER_CHANGE_CODE = 0xE9
    USER_CHANGE_PHONE_CODE = 0xEA

    ELEMENT_READ_NAME = 0xEE

    READ_RESULT = 0xEF


IntegraCommands = set( item.value for item in IntegraCommand )

IntegraPartsCommands = [
    IntegraCommand.READ_PARTS_ARMED_SUPPRESSED,
    IntegraCommand.READ_PARTS_ARMED_REALLY,
    IntegraCommand.READ_PARTS_ARMED_MODE_2,
    IntegraCommand.READ_PARTS_ARMED_MODE_3,
    IntegraCommand.READ_PARTS_1ST_CODE_ENTERED,
    IntegraCommand.READ_PARTS_ENTRY_TIME,
    IntegraCommand.READ_PARTS_EXIT_TIME_ABOVE_10,
    IntegraCommand.READ_PARTS_EXIT_TIME_BELOW_10,
    IntegraCommand.READ_PARTS_TEMP_BLOCKED,
    IntegraCommand.READ_PARTS_BLOCKED_FOR_GUARD,
    IntegraCommand.READ_PARTS_ALARM,
    IntegraCommand.READ_PARTS_FIRE_ALARM,
    IntegraCommand.READ_PARTS_ALARM_MEMORY,
    IntegraCommand.READ_PARTS_FIRE_ALARM_MEMORY,
    IntegraCommand.READ_PARTS_WITH_VIOLATED_ZONES,
    IntegraCommand.READ_PARTS_WITH_VERIFIED_ALARMS,
    IntegraCommand.READ_PARTS_ARMED_MODE_1,
    IntegraCommand.READ_PARTS_WITH_WARNING_ALARMS,
]

IntegraZonesCommands = [
    IntegraCommand.READ_ZONES_VIOLATION,
    IntegraCommand.READ_ZONES_TAMPER,
    IntegraCommand.READ_ZONES_ALARM,
    IntegraCommand.READ_ZONES_TAMPER_ALARM,
    IntegraCommand.READ_ZONES_ALARM_MEMORY,
    IntegraCommand.READ_ZONES_TAMPER_ALARM_MEMORY,
    IntegraCommand.READ_ZONES_BYPASS,
    IntegraCommand.READ_ZONES_NO_VIOLATION_TROUBLE,
    IntegraCommand.READ_ZONES_LONG_VIOLATION_TROUBLE,
    IntegraCommand.READ_ZONES_ISOLATE,
    IntegraCommand.READ_ZONES_MASKED,
    IntegraCommand.READ_ZONES_MASKED_MEMORY
]

IntegraOutputsCommands = [
    IntegraCommand.READ_OUTPUTS_STATE
]


class IntegraRtcStatus( Flag ):
    NONE = 0
    SERVICE_MODE = 1
    TROUBLES = 2
    ACU_100_PRESENT = 4
    INT_RX_PRESENT = 8
    TROUBLES_MEMORY = 16
    GRADE23_SET = 32


class IntegraCommandHelper:

    @staticmethod
    def cmds_from_bytes( cmds_data: bytes, bit_length ) -> list[ IntegraCommand ]:
        cmds_int = IntegraHelper.list_from_bytes( cmds_data, bit_length, False )
        cmds = [ ]
        for cmd_int in cmds_int:
            if cmd_int in IntegraCommands:
                cmds.append( IntegraCommand( cmd_int ) )
        return cmds

    @staticmethod
    def cmds_to_bytes( cmds: list[ IntegraCommand ] | None, bit_length: int = 48 ) -> bytes:
        cmds = [ ] if cmds is None else cmds
        cmds_int = [ item.value for item in cmds ]
        return IntegraHelper.list_to_bytes( cmds_int, bit_length, False )


_DT = TypeVar( "_DT", 'IntegraCmdData', type( IntegraEntityData ) )


class IntegraCmdData( IntegraEntityData ):
    _registry: dict[ IntegraCommand, _DT ] = { }
    _commands: list[ IntegraCommand ] = [ ]

    @classmethod
    def _register( cls, cmds: list[ IntegraCommand ], handler_class ) -> None:
        cls._registry.update( { (cmd, handler_class) for cmd in cmds } )
        return None

    @classmethod
    def register( cls ) -> None:
        if cls._commands:
            IntegraCmdData._register( cls._commands, cls )
        return None

    @classmethod
    def from_command( cls, cmd: IntegraCommand, data: bytes ) -> 'IntegraCmdData | None':
        class_ = None
        if cmd in cls._registry:
            class_ = cls._registry[ cmd ]
            result = class_()
            if isinstance( result, IntegraCmdData ):
                result._read_bytes( data, len( data ) )
            return result
        return None

    def __init__( self ):
        super().__init__()
        self._bytes: bytes = bytes()

    @property
    def bytes( self ) -> bytes:
        return self._bytes

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._bytes = payload


class IntegraCmdResultData( IntegraCmdData ):
    _commands = [ IntegraCommand.READ_RESULT ]

    def __init__( self ):
        super().__init__()
        self._error_code_no = 0

    @property
    def error_code_no( self ) -> int:
        return self._error_code_no

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._error_code_no = payload[ 0 ] if payload_len > 0 else 256


class IntegraCmdZonesData( IntegraCmdData ):
    _commands = [
        IntegraCommand.READ_ZONES_VIOLATION,
        IntegraCommand.READ_ZONES_TAMPER,
        IntegraCommand.READ_ZONES_ALARM,
        IntegraCommand.READ_ZONES_TAMPER_ALARM,
        IntegraCommand.READ_ZONES_ALARM_MEMORY,
        IntegraCommand.READ_ZONES_TAMPER_ALARM_MEMORY,
        IntegraCommand.READ_ZONES_BYPASS,
        IntegraCommand.READ_ZONES_NO_VIOLATION_TROUBLE,
        IntegraCommand.READ_ZONES_LONG_VIOLATION_TROUBLE,
        IntegraCommand.READ_ZONES_ISOLATE,
        IntegraCommand.READ_ZONES_MASKED,
        IntegraCommand.READ_ZONES_MASKED_MEMORY,

    ]

    def __init__( self ):
        super().__init__()
        self._zones: list[ int ] = [ ]

    @property
    def zones( self ) -> list[ int ]:
        return self._zones

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._zones = IntegraHelper.zones_from_bytes( payload )


class IntegraCmdPartsData( IntegraCmdData ):
    _commands = [
        IntegraCommand.READ_PARTS_ARMED_SUPPRESSED,
        IntegraCommand.READ_PARTS_ARMED_REALLY,
        IntegraCommand.READ_PARTS_ARMED_MODE_2,
        IntegraCommand.READ_PARTS_ARMED_MODE_3,
        IntegraCommand.READ_PARTS_1ST_CODE_ENTERED,
        IntegraCommand.READ_PARTS_ENTRY_TIME,
        IntegraCommand.READ_PARTS_EXIT_TIME_ABOVE_10,
        IntegraCommand.READ_PARTS_EXIT_TIME_BELOW_10,
        IntegraCommand.READ_PARTS_TEMP_BLOCKED,
        IntegraCommand.READ_PARTS_BLOCKED_FOR_GUARD,
        IntegraCommand.READ_PARTS_ALARM,
        IntegraCommand.READ_PARTS_FIRE_ALARM,
        IntegraCommand.READ_PARTS_ALARM_MEMORY,
        IntegraCommand.READ_PARTS_FIRE_ALARM_MEMORY,
        IntegraCommand.READ_PARTS_WITH_VIOLATED_ZONES,
        IntegraCommand.READ_PARTS_WITH_VERIFIED_ALARMS,
        IntegraCommand.READ_PARTS_ARMED_MODE_1,
        IntegraCommand.READ_PARTS_WITH_WARNING_ALARMS,
    ]

    def __init__( self ):
        super().__init__()
        self._parts: list[ int ] = [ ]

    @property
    def parts( self ) -> list[ int ]:
        return self._parts

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._parts = IntegraHelper.parts_from_bytes( payload )


class IntegraCmdOutputsData( IntegraCmdData ):
    _commands = [
        IntegraCommand.READ_OUTPUTS_STATE
    ]

    def __init__( self ):
        super().__init__()
        self._outputs: list[ int ] = [ ]

    @property
    def outputs( self ) -> list[ int ]:
        return self._outputs

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._outputs = IntegraHelper.outputs_from_bytes( payload )


class IntegraCmdDoorsData( IntegraCmdData ):
    _commands = [
        IntegraCommand.READ_DOORS_OPENED,
        IntegraCommand.READ_DOORS_OPENED_LONG
    ]

    def __init__( self ):
        super().__init__()
        self._doors: list[ int ] = [ ]

    @property
    def doors( self ) -> list[ int ]:
        return self._doors

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._doors = IntegraHelper.doors_from_bytes( payload )


class IntegraCmdTroublesData( IntegraCmdData ):
    _commands = [
        IntegraCommand.READ_TROUBLES_PART1,
        IntegraCommand.READ_TROUBLES_PART2,
        IntegraCommand.READ_TROUBLES_PART3,
        IntegraCommand.READ_TROUBLES_PART4,
        IntegraCommand.READ_TROUBLES_PART5,
        IntegraCommand.READ_TROUBLES_PART6,
        IntegraCommand.READ_TROUBLES_PART7,
        IntegraCommand.READ_TROUBLES_PART8,
    ]

    def __init__( self ):
        super().__init__()


class IntegraCmdTroublesMemoryData( IntegraCmdData ):
    _commands = [
        IntegraCommand.READ_TROUBLES_MEMORY_PART1,
        IntegraCommand.READ_TROUBLES_MEMORY_PART2,
        IntegraCommand.READ_TROUBLES_MEMORY_PART3,
        IntegraCommand.READ_TROUBLES_MEMORY_PART4,
        IntegraCommand.READ_TROUBLES_MEMORY_PART5,
        IntegraCommand.READ_TROUBLES_MEMORY_PART6,
        IntegraCommand.READ_TROUBLES_MEMORY_PART7,
        IntegraCommand.READ_TROUBLES_MEMORY_PART8,
    ]

    def __init__( self ):
        super().__init__()


class IntegraCmdDateVersionData( IntegraCmdData ):

    def __init__( self ):
        super().__init__()
        self._major: int = 0
        self._minor: int = 0
        self._date: datetime = datetime.min

    @property
    def major( self ) -> int:
        return self._major

    @property
    def minor( self ) -> int:
        return self._minor

    @property
    def date( self ) -> datetime:
        return self._date

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Version": f"{self.major:01d}.{self._minor:02d}",
            "Date": f"'{self.date}'",
        } )


class IntegraCmdVersionData( IntegraCmdDateVersionData ):
    _commands = [ IntegraCommand.READ_INTEGRA_VERSION ]

    def __init__( self ):
        super().__init__()
        self._integra_type: IntegraType = IntegraType.INTEGRA_UNKNOWN
        self._lang: IntegraLang = IntegraLang.UN
        self._in_flash: bool = False

    @property
    def integra_type( self ) -> IntegraType:
        return self._integra_type

    @property
    def lang( self ) -> IntegraLang:
        return self._lang

    @property
    def in_flash( self ) -> bool:
        return self._in_flash

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Type": f"{self.integra_type.name}",
            "Lang": f"{self.lang.name}",
            "InFlash": f"{self.in_flash}"
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._integra_type = IntegraType( payload[ 0 ] ) if payload_len > 0 and payload[ 0 ] in IntegraTypes else IntegraType.INTEGRA_UNKNOWN
        self._major, self._minor, self._date = IntegraHelper.decode_version( payload[ 1:12 ] ) if payload_len > 12 else (0, 0, datetime.min)
        self._lang = IntegraLang( payload[ 12 ] ) if payload_len > 12 and (payload[ 12 ] in IntegraLangs) else IntegraLang.UN
        self._in_flash = (int( payload[ 13 ] ) == 0xFF) if payload_len > 13 else False


class IntegraCmdModuleVersionData( IntegraCmdDateVersionData ):
    _commands = [ IntegraCommand.READ_MODULE_VERSION ]

    def __init__( self ):
        super().__init__()
        self._caps = IntegraModuleCaps.MODULE_CAP_EMPTY

    @property
    def caps( self ) -> IntegraModuleCaps:
        return self._caps

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Caps": f"{self.caps}"
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._major, self._minor, self._date = IntegraHelper.decode_version( payload[ 0:11 ] ) if payload_len > 10 else (0, 0, datetime.min)
        self._caps = IntegraModuleCaps.MODULE_CAP_EMPTY
        if payload_len > 11:
            self._caps |= IntegraModuleCaps.MODULE_CAP_32BYTE if payload[ 11 ] & (1 << 0) else IntegraModuleCaps.MODULE_CAP_EMPTY
            self._caps |= IntegraModuleCaps.MODULE_CAP_TROUBLE8 if payload[ 11 ] & (1 << 1) else IntegraModuleCaps.MODULE_CAP_EMPTY
            self._caps |= IntegraModuleCaps.MODULE_CAP_ARM_NO_BYPASS if payload[ 11 ] & (1 << 2) else IntegraModuleCaps.MODULE_CAP_EMPTY


class IntegraCmdRawData( IntegraCmdData ):

    def __init__( self, data: bytes ):
        super().__init__()
        self._data = data

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Data": f"({len( self._data )}) [ {IntegraHelper.hex_str( self._data )}] ",
        } )

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_bytes( self._data )


class IntegraCmdEventTextData( IntegraCmdData ):
    _commands = [ IntegraCommand.EXEC_GET_EVENT_TEXT ]

    def __init__( self, event_code_full: int, show_long: bool ):
        super().__init__()
        self._event_code_full = event_code_full
        self._show_long = show_long

    @property
    def event_code_full( self ) -> int:
        return self._event_code_full

    @property
    def show_long( self ) -> int:
        return self._show_long

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "EventCodeFull": f"{self._event_code_full}",
            "ShowLong": f"{self._show_long}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        value = (0x8000 if self.show_long else 0x0000) | (self.event_code_full & 0x07FF)
        payload.put_byte( (value & 0xFF00) >> 8, value )


class IntegraCmdEventRecData( IntegraCmdData ):

    def __init__( self, last_event_index: int ):
        super().__init__()
        self._last_event_index = last_event_index & 0xFFFFFF

    @property
    def last_event_index( self ) -> int:
        return self._last_event_index

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( { "LastEventIndex": f"0x{self.last_event_index:06X} ({self.last_event_index})" } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( (self.last_event_index & 0xFF0000) >> 16,
                          (self.last_event_index & 0x00FF00) >> 8,
                          (self.last_event_index & 0x0000FF) >> 0 )


class IntegraCmdReadElementData( IntegraCmdData ):

    def __init__( self, element_class: type[ IntegraElement ], element_no: int ):
        super().__init__()
        self._element_class: type[ IntegraElement ] = element_class
        self._element_type: IntegraElementType = element_class.element_type
        self._element_no: int = element_no

    @property
    def element_id( self ) -> int:
        if self._element_class == IntegraExpanderElement:
            return self._element_no + 0x80
        elif self._element_class == IntegraManipulatorElement:
            return self._element_no + 0xC0
        elif self._element_class == IntegraAdminElement:
            return self._element_no + 0xF0
        return self._element_no

    @property
    def element_no( self ) -> int:
        return self._element_no

    @property
    def element_type( self ) -> IntegraElementType:
        return self._element_type

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ElementType": f"{self.element_type.name}",
            "ElementNo": self.element_no
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( self.element_type.value, self.element_id )


class IntegraCmdUserCodeData( IntegraCmdData ):

    def __init__( self, user_code: str, prefix_code: str ):
        super().__init__()
        self._user_code = user_code
        self._prefix_code = prefix_code

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserCode": f"'{self.user_code}'",
            "PrefixCode": f"'{self.prefix_code}'"
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.user_code_to_bytes( self.user_code, self.prefix_code ) )

    @property
    def user_code( self ) -> str:
        return self._user_code

    @property
    def prefix_code( self ) -> str:
        return self._prefix_code


class IntegraCmdUserCodeNoData( IntegraCmdUserCodeData ):
    def __init__( self, user_no: int, user_code: str, prefix_code: str ):
        super().__init__( user_code, prefix_code )
        self._user_no: int = user_no

    @property
    def user_no( self ) -> int:
        return self._user_no

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserNo": f"{self.user_no}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( self.user_no )


class IntegraCmdUserPartsData( IntegraCmdUserCodeData ):

    def __init__( self, user_code: str, prefix_code: str, parts: list[ int ] ):
        super().__init__( user_code, prefix_code )
        self._parts = parts

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Parts": f"{self.parts}"
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.parts_to_bytes( self.parts ) )

    @property
    def parts( self ) -> list[ int ]:
        return self._parts


class IntegraCmdUserPartsArmData( IntegraCmdUserPartsData ):

    def __init__( self, user_code: str, prefix_code: str, parts: list[ int ], without_bypass_and_delay: bool | None = None ):
        super().__init__( user_code, prefix_code, parts )
        self._without_bypass_and_delay = without_bypass_and_delay

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "WithoutBypassAndDelay": f"{self.without_bypass_and_delay}"
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        if self.without_bypass_and_delay is not None:
            payload.put_byte( 0x80 if self.without_bypass_and_delay else 0x00 )

    @property
    def without_bypass_and_delay( self ) -> bool | None:
        return self._without_bypass_and_delay


class IntegraCmdUserZonesData( IntegraCmdUserCodeData ):

    def __init__( self, user_code: str, prefix_code: str, zones: list[ int ], zones_size: int = 128 ):
        super().__init__( user_code, prefix_code )
        self._zones = zones
        self._zones_size = zones_size

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Zones": f"{self.zones}",
            "ZonesSize": f"{self._zones_size}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.zones_to_bytes( self._zones, self.zones_size ) )

    @property
    def zones( self ) -> list[ int ]:
        return self._zones

    @property
    def zones_size( self ) -> int:
        return self._zones_size


class IntegraCmdUserSetUserLocksData( IntegraCmdUserCodeData ):

    def __init__( self, user_locks: IntegraUserLocks, user_code: str, prefix_code: str ) -> None:
        super().__init__( user_code, prefix_code )
        self._user_locks = user_locks

    @property
    def user_locks( self ) -> IntegraUserLocks:
        return self._user_locks

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserLocks": f"{self._user_locks}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( self.user_locks.to_bytes() )


class IntegraCmdUserDevMgmtData( IntegraCmdUserCodeData ):

    def __init__( self, func: IntegraUserDeviceMgmtFunc, user_code: str, prefix_code: str ) -> None:
        super().__init__( user_code, prefix_code )
        self._func = func

    @property
    def func( self ) -> IntegraUserDeviceMgmtFunc:
        return self._func

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Func": f"{self._func.name}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( self.func )


class IntegraCmdUserDevMgmtDeviceData( IntegraCmdUserDevMgmtData ):

    def __init__( self, device: IntegraUserDevice, func: IntegraUserDeviceMgmtFunc, user_code: str, prefix_code: str ) -> None:
        super().__init__( func, user_code, prefix_code )
        self._device = device

    @property
    def device( self ) -> IntegraUserDevice:
        return self._device

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Device": f"{self._device}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( self.device.to_bytes() )


class IntegraCmdUserDevMgmtUserData( IntegraCmdUserDevMgmtData ):

    def __init__( self, user_no: int, func: IntegraUserDeviceMgmtFunc, user_code: str, prefix_code: str ) -> None:
        super().__init__( func, user_code, prefix_code )
        self._user_no = user_no

    @property
    def user_no( self ) -> int:
        return self._user_no

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserNo": f"{self._user_no}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( self.user_no )


class IntegraUserDevMgmt( IntegraCmdData ):
    def __init__( self ) -> None:
        super().__init__()
        self._func = IntegraUserDeviceMgmtFunc.UNKNOWN

    @property
    def func( self ) -> IntegraUserDeviceMgmtFunc:
        return self._func

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Func": f"{self.func.name}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._func = IntegraUserDeviceMgmtFunc( payload[ 0 ] ) if payload_len > 0 and payload[ 0 ] in IntegraUserDeviceMgmtFuncs else IntegraUserDeviceMgmtFunc.UNKNOWN


class IntegraUserDevMgmtList( IntegraUserDevMgmt ):

    def __init__( self ) -> None:
        super().__init__()
        self._proximity_cards: list[ int ] = [ ]
        self._dallas_cards: list[ int ] = [ ]

    @property
    def proximity_cards( self ) -> list[ int ]:
        return self._proximity_cards

    @property
    def dallas_cards( self ) -> list[ int ]:
        return self._dallas_cards

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ProximityCards": f"{self._proximity_cards}",
            "DallasCards": f"{self._dallas_cards}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._proximity_cards = IntegraHelper.users_no_from_bytes( payload[ 1: 32 ] ) if payload_len > 31 else [ ]
        self._dallas_cards = IntegraHelper.users_no_from_bytes( payload[ 32: 63 ] ) if payload_len > 62 else [ ]


class IntegraCmdUserCodeUserData( IntegraCmdUserCodeData ):

    def __init__( self, user: IntegraUser, creating: bool, user_code: str, prefix_code: str ) -> None:
        super().__init__( user_code, prefix_code )
        self._user = user
        self.creating = creating

    @property
    def user( self ) -> IntegraUser:
        return self._user

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "User": f"{self._user}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( self.user.to_bytes() )
        if self.creating:
            payload.put_byte( self.user.object_no )


class IntegraCmdUserCodeNewCodeData( IntegraCmdUserCodeData ):

    def __init__( self, code_new: str, code_max_len: int, user_code: str, prefix_code: str ) -> None:
        super().__init__( user_code, prefix_code )
        self._code_new: str = code_new
        self._code_max_len: int = code_max_len

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.code_to_bytes( self._code_new, self._code_max_len ) )


class IntegraCmdUserCodeNewCodeUserData( IntegraCmdUserCodeNewCodeData ):

    def __init__( self, user_code_new: str, user_code: str, prefix_code: str ) -> None:
        super().__init__( user_code_new, 8, user_code, prefix_code )

    @property
    def user_code_new( self ) -> str:
        return self._code_new

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserCodeNew": f"'{self._code_new[ :self._code_max_len ]}'",
        } )


class IntegraCmdUserCodeNewCodePhoneData( IntegraCmdUserCodeNewCodeData ):

    def __init__( self, phone_code_new: str, user_code: str, prefix_code: str ) -> None:
        super().__init__( phone_code_new, 4, user_code, prefix_code )

    @property
    def phone_code_new( self ) -> str:
        return self._code_new

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "PhoneCodeNew": f"'{self._code_new[ :self._code_max_len ]}'",
        } )


class IntegraCmdElementData( IntegraCmdData ):

    def __init__( self, output_no: int = -1 ):
        super().__init__()
        self._output_no = output_no

    @property
    def output_no( self ) -> int:
        return self._output_no

    @property
    def output_id( self ) -> int:
        return IntegraHelper.output_to_byte( self.output_no )

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ElementId": f"{self.output_id}",
            "ElementNo": f"{self.output_no}"
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( self.output_id )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._output_no = int( IntegraHelper.output_from_byte( payload[ 0 ] ) ) if payload_len > 0 else 0

class IntegraCmdOutputData( IntegraCmdElementData ):

    def __init__( self, output_no: int = -1 ):
        super().__init__( output_no )

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.pop( "ElementNo", None )
        fields.pop( "ElementId", None )
        fields.update( {
            "OutputId": f"{self.output_id}",
            "OutputNo": f"{self.output_no}"
        } )


class IntegraCmdOutputPower( IntegraCmdOutputData ):
    _commands = [ IntegraCommand.READ_OUTPUT_POWER ]

    def __init__( self ):
        super().__init__()
        self._power = -1.0

    @property
    def power( self ) -> float:
        return self._power

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( { "Power": f"{self.power:.1f}" } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._power = float( int.from_bytes( payload[ 1: 3 ] ) / 10.0 ) if payload_len > 1 else -1.0


class IntegraCmdZoneData( IntegraCmdElementData ):

    def __init__( self, zone_no: int = -1 ):
        super().__init__( zone_no )

    @property
    def zone_no( self ):
        return self.output_no

    @property
    def zone_id( self ) -> int:
        return self.output_id

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.pop( "ElementNo", None )
        fields.pop( "ElementId", None )
        fields.update( {
            "ZoneId": f"{self.zone_id}",
            "ZoneNo": f"{self.zone_no}"
        } )


class IntegraCmdZoneTemp( IntegraCmdZoneData ):
    _commands = [ IntegraCommand.READ_ZONE_TEMPERATURE ]

    def __init__( self ):
        super().__init__()
        self._temp = 32712.5

    @property
    def temp( self ) -> float:
        return self._temp

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( { "Temp": f"{self.temp:.1f}" } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._temp = float( (int.from_bytes( payload[ 1: 3 ] ) - 0x6E) / 2.0 ) if payload_len > 1 else 32712.5

class IntegraCmdUserOutputsData( IntegraCmdUserCodeData ):

    def __init__( self, user_code: str, prefix_code: str, outputs: list[ int ], outputs_size: int ):
        super().__init__( user_code, prefix_code )
        self._outputs: list[ int ] = outputs
        self._outputs_size: int = outputs_size

    @property
    def outputs( self ) -> list[ int ]:
        return self._outputs

    @property
    def outputs_size( self ) -> int:
        return self._outputs_size

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Outputs": f"{self.outputs}",
            "OutputsSize": f"{self.outputs_size}" }
        )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.outputs_to_bytes( self.outputs, self.outputs_size ) )


class IntegraCmdUserOutputsExpandersData( IntegraCmdUserOutputsData ):

    def __init__( self, user_code: str, prefix_code: str, expanders: list[ int ] | None, outputs: list[ int ] | None = None, outputs_size: int = 128 ):
        super().__init__( user_code, prefix_code, [ ] if outputs is None else outputs, outputs_size )
        self._expanders: list[ int ] = [ ] if expanders is None else expanders

    @property
    def expanders( self ) -> list[ int ]:
        return self._expanders

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( { "Expanders": f"{self._expanders}" } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.expanders_to_bytes( self._expanders ) )

class IntegraCmdUserParts1stCodeData( IntegraCmdUserPartsData ):

    def __init__( self, user_code: str, prefix_code: str, parts: list[ int ], action: Integra1stCodeAction, validity_period: int ):
        super().__init__( user_code, prefix_code, parts )
        self._validity_period = validity_period
        self._action: Integra1stCodeAction = action

    @property
    def validity_period( self ) -> int:
        return self._validity_period

    @property
    def action( self ) -> Integra1stCodeAction:
        return self._action

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Action": f"{self._action.name}",
            "ValidityPeriod": f"{self._validity_period}",
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_byte( self.validity_period, (self.validity_period >> 8), self.action.value )

class IntegraCmdUserSetRtcData( IntegraCmdUserCodeData ):

    def __init__( self, user_code: str, prefix_code: str, date: datetime ):
        super().__init__( user_code, prefix_code )
        self._date = date

    @property
    def date( self ) -> datetime:
        return self._date

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Date": f"'{self.date}'"
        } )

    def _write_bytes( self, payload: IntegraBuffer ) -> None:
        super()._write_bytes( payload )
        payload.put_bytes( format( self.date, "%Y%m%d%H%M%S" ).encode() )


class IntegraCmdRtcData( IntegraCmdData ):
    _commands = [ IntegraCommand.READ_RTC_AND_STATUS ]

    def __init__( self ):
        super().__init__()
        self._rtc: datetime = datetime.min
        self._dow: IntegraDoW = IntegraDoW.Monday
        self._status: IntegraRtcStatus = IntegraRtcStatus.NONE
        self._integra_type: IntegraBaseType = IntegraBaseType.INTEGRA_UNKNOWN

    @property
    def rtc( self ) -> datetime:
        return self._rtc

    @property
    def dow( self ) -> IntegraDoW:
        return self._dow

    @property
    def status( self ) -> IntegraRtcStatus:
        return self._status

    @property
    def integra_type( self ) -> IntegraBaseType:
        return self._integra_type

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "RTC": f"'{self.rtc}'",
            "DoW": f"{self.dow.name}",
            "Status": f"{self.status}",
            "Type": f"{self.integra_type.name}"
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._rtc = IntegraHelper.decode_date_hex( payload[ 0:7 ] ) if payload_len > 6 else None
        self._dow = IntegraDoW( (payload[ 7 ] & 0x07) % 7 ) if payload_len > 7 else IntegraDoW.Monday
        self._status = IntegraRtcStatus.NONE
        self._integra_type = IntegraBaseType.INTEGRA_UNKNOWN

        if payload_len > 7:
            self._status |= IntegraRtcStatus.SERVICE_MODE if payload[ 7 ] & (1 << 7) else IntegraRtcStatus.NONE
            self._status |= IntegraRtcStatus.TROUBLES if payload[ 7 ] & (1 << 6) else IntegraRtcStatus.NONE

        if payload_len > 8:
            self._status |= IntegraRtcStatus.ACU_100_PRESENT if payload[ 8 ] & (1 << 7) else IntegraRtcStatus.NONE
            self._status |= IntegraRtcStatus.INT_RX_PRESENT if payload[ 8 ] & (1 << 6) else IntegraRtcStatus.NONE
            self._status |= IntegraRtcStatus.TROUBLES_MEMORY if payload[ 8 ] & (1 << 5) else IntegraRtcStatus.NONE
            self._status |= IntegraRtcStatus.GRADE23_SET if payload[ 8 ] & (1 << 4) else IntegraRtcStatus.NONE
            self._integra_type = IntegraBaseType( payload[ 8 ] & 0x0F ) if (payload[ 8 ] & 0x0F) in IntegraBaseTypes else IntegraBaseType.INTEGRA_UNKNOWN


def __register_decoders( source ):
    for module_item in source:
        if not module_item.startswith( "IntegraCmd" ):
            continue
        type_ = getattr( sys.modules[ __name__ ], module_item )
        try:
            if issubclass( type_, IntegraCmdData ) and type_ != IntegraCmdData:
                type_.register()
        except TypeError:
            continue


__register_decoders( dir() )
