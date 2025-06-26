from enum import Flag, IntEnum
from typing import Union

from .base import IntegraEntity
from .elements import IntegraZoneReactionType, IntegraExpanderType, IntegraManipulatorType, IntegraRadioType
from .notify import IntegraNotifyEvent
from .users import IntegraUserKind

class IntegraTroublesSystemMain( Flag ):
    NONE = 0x000000
    OUT1 = 0x000001
    OUT2 = 0x000002
    OUT3 = 0x000004
    OUT4 = 0x000008
    KPD = 0x000010
    EX1_2 = 0x000020
    BATT = 0x000040
    AC = 0x000080
    DT1 = 0x000100
    DT2 = 0x000200
    DTM = 0x000400
    RTC = 0x000800
    NO_DTR = 0x001000
    NO_BATT = 0x002000
    EXT_MODEM_INIT = 0x004000
    EXT_MODEM_CMD = 0x008000
    NO_VOLT_PHONE_LINE = 0x010000
    AUX_STM_CPU = 0x010000
    BAD_SIGNAL_PHONE_LINE = 0x020000
    NO_SIGNAL_PHONE_LINE = 0x040000
    MON_STA1 = 0x080000
    MON_STA2 = 0x100000
    EEPROM_OR_RTC_ACCESS = 0x200000
    RAM_MEMORY = 0x400000
    MAIN_PANEL_RESTART_MEM = 0x800000


class IntegraTroublesSystemOther( Flag ):
    NONE = 0x00
    NO_ETHM_CONN_MON_STA1 = 0x01
    NO_ETHM_CONN_MON_STA2 = 0x02
    NO_GPRS_CONN_MON_STA1 = 0x04
    NO_GPRS_CONN_MON_STA2 = 0x08
    TIME_SERVER = 0x10
    GSM_INIT = 0x20
    MON_IP_STA1 = 0x40
    MON_IP_STA2 = 0x80


IntegraTroublesDataType = Union[dict[ int, bool ]|IntegraTroublesSystemMain|IntegraTroublesSystemOther]

class IntegraTroublesZone( Flag ):
    NONE = 0x00
    TECHNICAL = 0x01
    TECHNICAL_MEMORY = 0x02


class IntegraTroublesExp( Flag ):
    NONE = 0x00
    AC = 0x01
    OUTPUT_OVERLOAD = 0x02
    BATT = 0x04
    NO_BATT = 0x08
    CARD_READER_HEAD_A = 0x10
    CARD_READER_HEAD_B = 0x20
    BUSY = 0x40
    ACU_SYNCHRO = 0x80
    NO_KNX_CONN = 0x100
    HIGH_BATT_RES = 0x200
    BATT_CHARGING = 0x400
    SUPPLY_OUTPUT_OVERLOAD = 0x800
    ACU_JAMMED = 0x1000
    ADDRESSABLE_ZONE_EXP_SHORT_CIRCUIT = 0x2000
    EXP_NO_COMM = 0x4000
    SUBSTED = 0x8000
    TAMPER = 0x10000


class IntegraTroublesMan( Flag ):
    NONE = 0x00
    PING = 0x01
    AC = 0x02
    MAC_ID_SRV = 0x04
    IMEI_ID_SRV = 0x08
    BAT1 = 0x10
    BAT2 = 0x20
    BATT = 0x40
    CONN_SRV = 0x80
    MAN_NO_COMM = 0x100
    SUBSTED = 0x200
    NO_LAN_CABLE = 0x400
    NO_DSR_SIGNAL = 0x800
    TAMPER = 0x1000
    INIT_FAILED = 0x2000
    AUX_STM = 0x4000


class IntegraTroublesUsr( Flag ):
    NONE = 0x00
    LOW_BATTERY = 0x01


class IntegraTroublesRadio( Flag ):
    NONE = 0x00
    MODULE_JAM_LEVEL = 0x01
    LOW_BATTERY = 0x02
    DEVICE_NO_COMM = 0x04
    OUTPUT_NO_COMM = 0x08


class IntegraTroublesSource( IntEnum ):
    ZONES = 0
    EXPANDERS = 1
    MANIPULATORS = 2
    SYSTEM_MAIN = 3
    SYSTEM_OTHER = 4
    RADIO = 5
    USERS = 6
    INT_GSM = 7


class IntegraTroublesRegionId( IntEnum ):
    P1_R1 = 101
    P1_R2 = 102
    P1_R3 = 103
    P1_R4 = 104
    P1_R5 = 105
    P1_R6 = 106
    P1_R7 = 107
    P1_R8 = 108
    P1_R9 = 109

    P2_R1 = 201
    P2_R2 = 202
    P2_R3 = 203
    P2_R4 = 204

    P3_R1 = 301
    P3_R2 = 302
    P3_R3 = 303
    P3_R4 = 304

    P4_R1 = 401
    P4_R2 = 402
    P4_R3 = 403
    P4_R4 = 404
    P4_R5 = 405
    P4_R6 = 406
    P4_R7 = 407
    P4_R8 = 408
    P4_R9 = 409

    P5_R1 = 501
    P5_R2 = 502

    P6_R1 = 601
    P6_R2 = 602
    P6_R3 = 601

    P7_R1 = 701
    P7_R2 = 702
    P7_R3 = 701

    P8_R1 = 801
    P8_R2 = 802
    P8_R3 = 803
    P8_R4 = 804
    P8_R5 = 805
    P8_R6 = 806
    P8_R7 = 807
    P8_R8 = 808


class IntegraTroublesRegionDef( IntegraEntity ):

    def __init__( self, notify_event: IntegraNotifyEvent, region_id: IntegraTroublesRegionId, offset: int, size: int, source: IntegraTroublesSource, values: dict[ IntEnum, Flag ] | None ):
        super().__init__()
        self._notify_event: IntegraNotifyEvent = notify_event
        self._region_id: IntegraTroublesRegionId = region_id
        self._offset: int = offset
        self._size: int = size
        self._source: IntegraTroublesSource = source
        self._values: dict[ IntEnum, Flag ] | None = values

    @property
    def notify_event( self ) -> IntegraNotifyEvent:
        return self._notify_event

    @property
    def region_id( self ) -> IntegraTroublesRegionId:
        return self._region_id

    @property
    def offset( self ) -> int:
        return self._offset

    @property
    def size( self ) -> int:
        return self._size

    @property
    def source( self ) -> IntegraTroublesSource:
        return self._source

    @property
    def values( self ) -> dict:
        return self._values

    def get_data( self, source: bytes ) -> bytes:
        return source[ self._offset:self._offset + self._size ]


class IntegraTroublesRegionDefs( IntegraEntity ):

    def __init__( self ):
        super().__init__()

    __REGIONS: dict[ IntegraNotifyEvent, list[ IntegraTroublesRegionDef ] ] = {
        IntegraNotifyEvent.TROUBLES_PART1: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R1, 0, 16, IntegraTroublesSource.ZONES, {
                IntegraZoneReactionType.ANY: IntegraTroublesZone.TECHNICAL } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R2, 16, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.OTHER: IntegraTroublesExp.AC } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R3, 24, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.CA_64_DR: IntegraTroublesExp.OUTPUT_OVERLOAD,
                IntegraExpanderType.CA_64_SR: IntegraTroublesExp.OUTPUT_OVERLOAD,
                IntegraExpanderType.OTHER: IntegraTroublesExp.BATT } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R4, 32, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.OTHER: IntegraTroublesExp.NO_BATT } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R5, 40, 3, IntegraTroublesSource.SYSTEM_MAIN, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R6, 43, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.ETHM_1: IntegraTroublesMan.PING,
                IntegraManipulatorType.INT_PTSA: IntegraTroublesMan.AC } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R7, 44, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.ETHM_1: IntegraTroublesMan.MAC_ID_SRV,
                IntegraManipulatorType.INT_GSM: IntegraTroublesMan.IMEI_ID_SRV,
                IntegraManipulatorType.INT_KWRL: IntegraTroublesMan.BAT1,
                IntegraManipulatorType.INT_PTSA: IntegraTroublesMan.BATT } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R8, 45, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.ETHM_1: IntegraTroublesMan.CONN_SRV,
                IntegraManipulatorType.INT_KWRL: IntegraTroublesMan.BAT2 } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART1, IntegraTroublesRegionId.P1_R9, 46, 1, IntegraTroublesSource.SYSTEM_OTHER, None )
        ],

        IntegraNotifyEvent.TROUBLES_PART2: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART2, IntegraTroublesRegionId.P2_R1, 0, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.CA_64_SR: IntegraTroublesExp.CARD_READER_HEAD_A,
                IntegraExpanderType.ACU_100: IntegraTroublesExp.ACU_SYNCHRO,
                IntegraExpanderType.INT_TXM: IntegraTroublesExp.BUSY,
                IntegraExpanderType.INT_KNX: IntegraTroublesExp.NO_KNX_CONN,
                IntegraExpanderType.OTHER: IntegraTroublesExp.HIGH_BATT_RES } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART2, IntegraTroublesRegionId.P2_R2, 8, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.CA_64_SR: IntegraTroublesExp.CARD_READER_HEAD_B,
                IntegraExpanderType.OTHER: IntegraTroublesExp.BATT_CHARGING } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART2, IntegraTroublesRegionId.P2_R3, 16, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.OTHER: IntegraTroublesExp.SUPPLY_OUTPUT_OVERLOAD } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART2, IntegraTroublesRegionId.P2_R4, 24, 2, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.ACU_100: IntegraTroublesExp.ACU_JAMMED,
                IntegraExpanderType.OTHER: IntegraTroublesExp.ADDRESSABLE_ZONE_EXP_SHORT_CIRCUIT } )
        ],

        IntegraNotifyEvent.TROUBLES_PART3: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART3, IntegraTroublesRegionId.P3_R1, 0, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.MODULE_JAM_LEVEL } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART3, IntegraTroublesRegionId.P3_R2, 15, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.LOW_BATTERY } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART3, IntegraTroublesRegionId.P3_R3, 30, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.DEVICE_NO_COMM } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART3, IntegraTroublesRegionId.P3_R4, 45, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.OUTPUT_NO_COMM } )
        ],
        IntegraNotifyEvent.TROUBLES_PART4: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R1, 0, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.OTHER: IntegraTroublesExp.EXP_NO_COMM } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R2, 8, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.OTHER: IntegraTroublesExp.SUBSTED } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R3, 16, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraExpanderType.OTHER: IntegraTroublesMan.MAN_NO_COMM } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R4, 17, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraExpanderType.OTHER: IntegraTroublesMan.SUBSTED } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R5, 18, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.ETHM_1: IntegraTroublesMan.NO_LAN_CABLE,
                IntegraManipulatorType.INT_RS: IntegraTroublesMan.NO_DSR_SIGNAL } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R6, 19, 8, IntegraTroublesSource.EXPANDERS, {
                IntegraExpanderType.OTHER: IntegraTroublesExp.TAMPER } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R7, 27, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.OTHER: IntegraTroublesMan.TAMPER } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R8, 28, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.OTHER: IntegraTroublesMan.INIT_FAILED } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART4, IntegraTroublesRegionId.P4_R9, 29, 1, IntegraTroublesSource.MANIPULATORS, {
                IntegraManipulatorType.OTHER: IntegraTroublesMan.AUX_STM } )
        ],

        IntegraNotifyEvent.TROUBLES_PART5: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART5, IntegraTroublesRegionId.P5_R1, 0, 8, IntegraTroublesSource.USERS, {
                IntegraUserKind.OTHER: IntegraTroublesUsr.LOW_BATTERY } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART5, IntegraTroublesRegionId.P5_R2, 8, 8, IntegraTroublesSource.USERS, {
                IntegraUserKind.OTHER: IntegraTroublesUsr.LOW_BATTERY } )
        ],

        IntegraNotifyEvent.TROUBLES_PART6: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART6, IntegraTroublesRegionId.P6_R1, 0, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.LOW_BATTERY } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART6, IntegraTroublesRegionId.P6_R2, 15, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.DEVICE_NO_COMM } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART6, IntegraTroublesRegionId.P6_R3, 30, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.OUTPUT_NO_COMM } )
        ],

        IntegraNotifyEvent.TROUBLES_PART7: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART7, IntegraTroublesRegionId.P7_R1, 0, 16, IntegraTroublesSource.ZONES, {
                IntegraRadioType.OTHER: IntegraTroublesZone.TECHNICAL } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART7, IntegraTroublesRegionId.P7_R2, 16, 16, IntegraTroublesSource.ZONES, {
                IntegraRadioType.OTHER: IntegraTroublesZone.TECHNICAL_MEMORY } ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART7, IntegraTroublesRegionId.P7_R3, 32, 15, IntegraTroublesSource.RADIO, {
                IntegraRadioType.OTHER: IntegraTroublesRadio.MODULE_JAM_LEVEL } )
        ],

        IntegraNotifyEvent.TROUBLES_PART8: [
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R1, 0, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R2, 8, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R3, 16, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R4, 24, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R5, 32, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R6, 40, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R7, 48, 8, IntegraTroublesSource.INT_GSM, None ),
            IntegraTroublesRegionDef( IntegraNotifyEvent.TROUBLES_PART8, IntegraTroublesRegionId.P8_R8, 56, 8, IntegraTroublesSource.INT_GSM, None )
        ]
    }

    @classmethod
    def get_regions( cls, notify_event: IntegraNotifyEvent ) -> list[ IntegraTroublesRegionDef ]:
        if notify_event in cls.__REGIONS:
            return cls.__REGIONS[ notify_event ]
        return [ ]
