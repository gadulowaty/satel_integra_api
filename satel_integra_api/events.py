import datetime
from datetime import datetime

from enum import (
    IntEnum,
    Flag
)
from typing import Any

from .const import DEFAULT_CODE_PAGE
from .data import IntegraEntityData

INTEGRA_EVENT_MIN_LEN = 14
INTEGRA_EVENT_STD_LAST = 0xFFFFFF
INTEGRA_EVENT_GRADE_LAST = 0x00FFFF


class IntegraEventSource( IntEnum ):
    UNKNOWN = 0
    STANDARD = 1
    GRADE2 = 2


class IntegraEventMonStatus( IntEnum ):
    NEW = 0
    SENT = 1
    NOT_SENT = 2
    NOT_MONITORED = 3


class IntegraEventClass( IntEnum ):
    ZONE_AND_TAMPER_ALARMS = 0
    PART_AND_EXPANDER_ALARMS = 1
    ARMING_DISARMING__ALARM_CLEARING = 2
    ZONE_BYPASS_SET_UNSET = 3
    ACCESS_CONTROL = 4
    TROUBLES = 5
    USER_FUNCTIONS = 6
    SYSTEM_EVENTS = 7


class IntegraEventKindShort( Flag ):
    FLAG_NONE = 0x0000
    # s-partition
    PART_0 = 0x0001
    # e - zone/expander/LCD-keypad
    ZONE_EXPA_LCD_1 = 0x0002
    # u - user
    USER_2 = 0x0004
    # k - expander in RPPPPP
    EXPA_3 = 0x0008
    # m - LCD-keypad in PPPPP
    LCD_KEYPAD_4 = 0x0010
    # w - output/expander, partition only for expanders
    OUTPUT_EXPA_5 = 0x0020
    # t - timer
    TIMER_6 = 0x0040
    # g - proximity card reader
    PROX_CARD_READER_7 = 0x0080
    # T - telephone
    PHONE_NO_8 = 0x0100
    # n - number (RAM error)
    NUMBER_9 = 0x0200
    # D - data bus (0=DTM, 1=DT1, 2=DT2, 129..128+IL_EXPAND=expander)
    DATA_BUS_10 = 0x0400
    # o - call back (0='SERV', 1='SERV=', 2='USER', 3='USER=', 4='ETHM-modem', 5='ETHM-RS')
    CALL_BACK_11 = 0x0800
    # R - telephone relay
    PHONE_REL_12 = 0x1000
    # I - TCP/IP event (2 records !!!)
    TCP_IP_13 = 0x2000
    # r - ABAX input/output, partition only for input
    ABAX_14 = 0x4000
    # M - monitoring"
    MONITOR_15 = 0x8000


class IntegraEventRecData( IntegraEntityData ):
    source: IntegraEventSource = IntegraEventSource.UNKNOWN

    def __init__( self ):
        super().__init__()

        self._date: datetime = datetime.min
        self._no_more: bool = True

        # 1st byte
        self._year_marker: int = 0
        self._empty: bool = True
        self._present: bool = False
        self._monitoring_status2: IntegraEventMonStatus = IntegraEventMonStatus.NOT_MONITORED
        self._monitoring_status1: IntegraEventMonStatus = IntegraEventMonStatus.NOT_MONITORED

        # 2nd byte
        self._event_class: IntegraEventClass = IntegraEventClass.SYSTEM_EVENTS
        self._day: int = 0

        # 3rd byte
        self._month: int = 0

        # 4th byte
        self._minutes: int = 0

        # 5th byte
        self._part_no: int = 0
        self._restore: bool = False

        # 6th byte
        self._code: int = 0

        # 7th byte
        self._source_no: int = 0

        # 8th byte
        self._object_no: int = 0
        self._user_ctrl_no: int = 0

        self._index: int = 0
        self._index_called: int = 0

    @property
    def date( self ) -> datetime:
        return self._date

    @property
    def no_more( self ) -> bool:
        return self._no_more

    @property
    def year_marker( self ) -> int:
        return self._year_marker

    @property
    def empty_entity( self ) -> bool:
        return self._empty

    @property
    def present( self ) -> bool:
        return self._present

    @property
    def monitoring_status1( self ) -> IntegraEventMonStatus:
        return self._monitoring_status1

    @property
    def monitoring_status2( self ) -> IntegraEventMonStatus:
        return self._monitoring_status2

    @property
    def event_class( self ) -> IntegraEventClass:
        return self._event_class

    @property
    def day( self ) -> int:
        return self._day

    @property
    def month( self ) -> int:
        return self._month

    @property
    def minutes( self ) -> int:
        return self._minutes

    @property
    def part_no( self ) -> int:
        return self._part_no

    @property
    def restore( self ) -> bool:
        return self._restore

    @property
    def code( self ) -> int:
        return self._code

    @property
    def code_full( self ) -> int:
        return ((1 if self.restore else 0) << 10) | (self.code & 0x03FF)

    @property
    def source_no( self ) -> int:
        return self._source_no

    @property
    def object_no( self ) -> int:
        return self._object_no

    @property
    def user_ctrl_no( self ) -> int:
        return self._user_ctrl_no

    @property
    def index( self ) -> int:
        return self._index

    @property
    def index_called( self ) -> int:
        return self._index_called

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Date": f"'{self.date}'",
            "Source": f"{self.source.name}",
            "EventClass": f"{self.event_class.name}",
            "Empty": f"{self.empty_entity}",
            "Present": f"{self.present}",
            "Restore": f"{self.restore}",
            "Code": f"{self.code}",
            "CodeFull": f"{self.code_full}",
            "PartNo": f"{self.part_no}",
            "SourceNo": f"{self.source_no}",
            "ObjectNo": f"{self.object_no}",
            "UserCtrlNo": f"{self.user_ctrl_no}",
            "Index": f"0x{self.index:06X} ({self.index})",
            "IndexCall": f"0x{self.index_called:06X} ({self.index_called})",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ):
        if payload_len < INTEGRA_EVENT_MIN_LEN:
            return

        if self.source == IntegraEventSource.STANDARD:
            self._no_more = True if (payload[ 0 ] & 0x20) == 0 else False
        elif self.source == IntegraEventSource.GRADE2:
            self._no_more = True if payload[ 0 ] == 0 else False

        if not self._no_more:
            # 1st byte
            self._year_marker = ((payload[ 0 ] & 0xC0) >> 6)
            self._empty = (payload[ 0 ] & 0x20) == 0
            self._present = (payload[ 0 ] & 0x10) != 0
            self._monitoring_status2 = IntegraEventMonStatus( (payload[ 0 ] & 0x0C) >> 2 )
            self._monitoring_status1 = IntegraEventMonStatus( (payload[ 0 ] & 0x03) >> 0 )

            # 2nd byte
            self._event_class = IntegraEventClass( (payload[ 1 ] & 0xE0) >> 5 )
            self._day = (payload[ 1 ] & 0x1F)

            # 3rd byte
            self._month = ((payload[ 2 ] & 0xF0) >> 4)

            # 4th byte
            self._minutes = ((payload[ 2 ] & 0x0F) << 8) | payload[ 3 ]

            # 5th byte
            self._part_no = ((payload[ 4 ] & 0xF8) >> 3)
            self._restore = ((payload[ 4 ] & 0x04) != 0)

            # 6th byte
            self._code = ((payload[ 4 ] & 0x03) << 8) | payload[ 5 ]

            # 7th byte
            self._source_no = payload[ 6 ]

            # 8th byte
            self._object_no = ((payload[ 7 ] & 0xE0) >> 5)
            self._user_ctrl_no = (payload[ 7 ] & 0x1F)

        self._index = ((payload[ 8 ] & 0xFF) << 16) | ((payload[ 9 ] & 0xFF) << 8) | ((payload[ 10 ] & 0xFF) << 0)
        self._index_called = ((payload[ 11 ] & 0xFF) << 16) | ((payload[ 12 ] & 0xFF) << 8) | ((payload[ 13 ] & 0xFF) << 0)
        self._update()

    def _update( self ):
        current_year: int = datetime.now().year
        year_base: int = int( current_year / 4 )
        year: int = 4 * year_base + self._year_marker
        hour, minute = divmod( self.minutes, 60 )
        if year > current_year:
            year -= 4
        self._date = datetime( year, self.month, self.day, hour, minute )

class IntegraEventRecStdData( IntegraEventRecData ):
    source: IntegraEventSource = IntegraEventSource.STANDARD
    def __init__( self):
        super().__init__()

class IntegraEventRecGradeData( IntegraEventRecData ):
    source: IntegraEventSource = IntegraEventSource.GRADE2
    def __init__( self):
        super().__init__()

class IntegraEventTextData( IntegraEntityData ):

    def __init__( self ):
        super().__init__()
        self._restore: bool = False
        self._event_code: int = 0
        self._event_code_full: int = 0
        self._show_long: bool = False
        self._long_kind: int = 0
        self._short_kind: IntegraEventKindShort = IntegraEventKindShort.FLAG_NONE
        self._text: str = ""

    @property
    def restore( self ) -> bool:
        return self._restore

    @property
    def event_code( self ) -> int:
        return self._event_code

    @property
    def event_code_full( self ) -> int:
        return self._event_code_full

    @property
    def show_long( self ) -> bool:
        return self._show_long

    @property
    def long_kind( self ) -> int:
        return self._long_kind

    @property
    def short_kind( self ) -> IntegraEventKindShort:
        return self._short_kind

    @property
    def text( self ) -> str:
        return self._text

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "EventCodeFull": f"{self.event_code_full}",
            "EventCode": f"{self.event_code}",
            "ShowLong": f"{self.show_long}",
            "Restore": f"{self.restore}",
            "LongKind": f"{self.long_kind}",
            "ShortKind": f"{self.short_kind} (0x{self.short_kind.value:04X}) (b{self.short_kind.value:016b})",
            "Text": f"'{self.text}'"
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "code": self.event_code,
            "restore": self.restore,
            "show_long": self.show_long,
            "long_kind": self.long_kind,
            "short_kind": self.short_kind.value,
            "text": self.text
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._event_code = json_data["code"]
        self._restore = json_data["restore"]
        self._show_long = json_data["show_long"]
        self._long_kind = json_data["long_kind"]
        self._short_kind = json_data["short_kind"]
        self._text = json_data["text"]

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )

        value = ((payload[ 0 ] << 8) & 0xFF00) | (payload[ 1 ] & 0xFF) if payload_len > 1 else 0
        self._event_code_full = (value & 0x07FF)
        self._event_code = (value & 0x03FF)
        self._restore = True if self._event_code_full & 0x0400 != 0 else False
        self._show_long = True if value & 0x8000 != 0 else False
        self._long_kind = payload[ 2 ] if payload_len > 2 else 0
        self._short_kind = IntegraEventKindShort( (((payload[ 3 ] & 0xFF) << 8) | (payload[ 4 ] & 0xFF)) if payload_len > 4 else 0 )
        self._text = payload[ 5: ].decode( DEFAULT_CODE_PAGE ) if payload_len > 5 and payload[ 5 ] != 0 else "".ljust( 46 if self.show_long else 16 )
