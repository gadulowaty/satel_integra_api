import logging
import sys

from enum import (
    IntEnum,
    Flag
)
from typing import Any
from .const import DEFAULT_CODE_PAGE
from .data import IntegraEntityData
from .tools import IntegraHelper

_LOGGER = logging.getLogger( __name__ )


class IntegraElementType( IntEnum ):
    PARTITION = 0
    ZONE = 1
    USER = 2
    EXPANDER = 3
    MANIPULATOR = 3
    OUTPUT = 4
    ZONE_WITH_PARTS = 5
    TIMER = 6
    TELEPHONE = 7
    OBJECT = 15
    PARTITION_WITH_OBJ = 16
    OUTPUT_WITH_DURATION = 17
    PARTITION_WITH_OBJ_OPTS = 18
    PARTITION_WITH_OBJ_OPTS_DEPS = 19
    UNKNOWN = 255


IntegraElementTypes = set( item.value for item in IntegraElementType )


class IntegraPartType( IntEnum ):
    PASSWORD_PROTECTED = 0
    TIMER_BLOCKED = 1
    DEPENDENT_AND = 2
    DEPENDENT_OR = 3
    ACCESS_BY_TIMER_1_32 = 4
    ACCESS_BY_TIMER_33_64 = 5
    CONTROLLED_BY_TIMER_1_32 = 6
    CONTROLLED_BY_TIMER_33_64 = 7
    TREASURY = 8
    INVALID = 255


IntegraPartTypes = set( item.value for item in IntegraPartType )


class IntegraPartOptions( Flag ):
    NONE = 0
    TWO_CODES_TO_ARM = 1
    TWO_CODES_TO_DISARM = 2
    TIMER_PRIORITY = 4
    TWO_CODES_ON_TO_DEVICES = 8
    ALARM_VERIFICATION = 16
    EXIT_DELAY_CAN_BE_SHORTENED = 32
    INFINITE_EXIT_DELAY = 64
    CONST_1ST_CODE_VALIDITY_PERIOD = 128

    CONST_BLOCKING_TIME = 256
    DO_NOT_DISARM_IN_CASE_OF_ALARM = 512
    OPT_UNUSED2 = 1024
    OPT_UNUSED3 = 2048
    OPT_UNUSED4 = 4096
    OPT_UNUSED5 = 8192
    OPT_UNUSED6 = 16384
    AUTO_ARM_CAN_BE_DEFERRED = 32768


class IntegraAutoArmDeferStatus( IntEnum ):
    INACTIVE = 0
    DEFER_TIME_SET = 1
    TIMER_IS_RUNNING = 2


IntegraAutoArmDeferStatuses = set( item.value for item in IntegraAutoArmDeferStatus )

class IntegraRadioType(IntEnum ):
    OTHER = 0

class IntegraExpanderType( IntEnum ):
    UNKNOWN = 0
    OTHER = 0
    CA_64_PP = 1
    CA_64_E = 2
    CA_64_O = 3
    CA_64_EPS = 4
    CA_64_OPS = 5
    CA_64_ADR = 6
    INT_ORS = 7
    INT_S_SK = 8
    INT_SZ_SZK = 9
    CA_64_DR = 10
    CA_64_SR = 11
    ACU_100 = 12
    INT_IORS = 13
    CA_64_Ei = 14
    CA_64_SM = 15
    INT_AV = 16
    INT_IT = 17
    CA_64_EPSi = 18
    INT_SCR = 19
    INT_ENT = 20
    INT_RX = 21
    INT_TXM = 22
    INT_VG = 23
    INT_KNX = 24
    INT_PP = 25
    INT_ORSPS = 26
    INT_IORSPS = 27
    INT_ADR = 28


IntegraExpanderTypes = set( item.value for item in IntegraExpanderType )


class IntegraManipulatorType( IntEnum ):
    UNKNOWN = 0
    OTHER = 0
    INT_KLCD = 1
    INT_KLCDR = 2
    INT_PTSA = 3
    INT_RS = 4
    ETHM_1 = 5
    INT_KSG = 6
    INT_TSI = 8
    INT_TSG = 10
    INT_TSH = 12
    INT_KWRL = 14
    INT_GSM = 15
    ETHM_1_Plus_INT_GS = 16


IntegraManipulatorTypes = set( item.value for item in IntegraManipulatorType )


class IntegraElement( IntegraEntityData ):
    element_set: str = ""
    element_type: IntegraExpanderType = IntegraElementType.UNKNOWN

    def __init__( self ):
        super().__init__()
        self._element_no = -1
        self._name = ""
        self._valid = False

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ElementType": f"{self.element_type.name}",
            "ElementNo": f"{self.element_no}",
            "Name": f"'{self.name}'"
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        element_type: IntegraElementType = IntegraElementType( payload[ 0 ] ) if payload_len > 0 and payload[ 0 ] in IntegraElementTypes else None
        element_no: int = payload[ 1 ] if payload_len > 1 else -1
        if element_type is not None and self.element_type == element_type:
            self._element_no = element_no
            self._name = payload[ 3:19 ].decode( DEFAULT_CODE_PAGE ).rstrip( " " ) if payload_len > 18 else ""
            self._valid = True

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        json_data.update( {
            "element_no": self.element_no,
            "element_type": self.element_type,
            "name": self.name
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        self._type = IntegraElementType( json_data[ "element_type" ] )
        self._element_no = json_data[ "element_no" ]
        self._name = json_data[ "name" ]

    @property
    def valid( self ) -> bool:
        return self._valid

    @property
    def element_id( self ):
        return self._element_no

    @property
    def element_no( self ) -> int:
        return self._element_no

    @property
    def name( self ) -> str:
        return self._name

    @classmethod
    def empty_element( cls, element_no ) -> 'IntegraElement':
        result = cls()
        result._element_no = element_no
        return result


class IntegraElementFactory:
    _registry: dict[ str, dict[ IntegraExpanderType, type[ IntegraElement ] ] ] = { }

    @classmethod
    def register_class( cls, element_type: type[ IntegraElement ] ) -> None:
        if element_type.element_set != "" and element_type.element_type != IntegraElementType.UNKNOWN:
            by_name = cls._registry.setdefault( element_type.element_set, {} )
            by_name.update( { element_type.element_type: element_type } )

    @classmethod
    def get_class( cls, element_set: str, element_type: IntegraElementType ) -> type[ IntegraElement ]:
        by_name = cls._registry.get( element_set, None )
        if by_name is not None and element_type in by_name:
            return by_name[ element_type ]
        return IntegraElement

    @classmethod
    def exists( cls, element_set: str, element_type: IntegraElementType ) -> bool:
        by_name = cls._registry.get( element_set, None )
        if by_name is not None and element_type in by_name:
            return True
        return False


class IntegraPartElement( IntegraElement ):
    element_set = "parts"
    element_type = IntegraElementType.PARTITION

    def __init__( self ):
        super().__init__()
        self._part_type = IntegraPartType.PASSWORD_PROTECTED

    @property
    def part_no( self ) -> int:
        return self.element_no

    @property
    def part_type( self ) -> IntegraPartType:
        return self._part_type

    def _set_part_type( self, value: int ) -> None:
        self._part_type = IntegraPartType( value & 0xFF ) if (value & 0xFF) in IntegraPartTypes else IntegraPartType.INVALID

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "PartNo": f"{self.part_no}",
            "PartType": f"{self.part_type}"
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._set_part_type( payload[ 2 ] )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "part_type": self.part_type,
            "part_type_name": self.part_type.name,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._set_part_type( json_data.get("part_type", -1 ) )


class IntegraPartWithObjElement( IntegraPartElement ):
    element_set = "parts"
    element_type: IntegraElementType = IntegraElementType.PARTITION_WITH_OBJ

    def __init__( self ):
        super().__init__()

        self._object_no: int = 0x00

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ObjectNo": f"{self.object_no}"
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "object_no": self.object_no,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._object_no = json_data[ "object_no" ]

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._object_no = payload[ 19 ] if payload_len > 19 else 0x00

    @property
    def object_no( self ) -> int:
        return self._object_no


class IntegraPartWithObjOptsElement( IntegraPartWithObjElement ):
    element_set = "parts"
    element_type = IntegraElementType.PARTITION_WITH_OBJ_OPTS

    def __init__( self ):
        super().__init__()
        self._options: IntegraPartOptions = IntegraPartOptions.NONE
        self._auto_arm_defer_status: IntegraAutoArmDeferStatus = IntegraAutoArmDeferStatus.INACTIVE
        self._auto_arm_defer_time: int = 0

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "AutoArmDeferStats": f"{self.auto_arm_defer_status.name}",
            "AutoArmDeferTime": f"{self.auto_arm_defer_time}"
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "options": self.options.value,
            "auto_arm_defer_status": self.auto_arm_defer_status,
            "auto_arm_defer_time": self.auto_arm_defer_time,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._options = IntegraPartOptions( json_data[ "options" ] )
        self._auto_arm_defer_status = IntegraAutoArmDeferStatus( json_data[ "auto_arm_defer_status" ] )
        self._auto_arm_defer_time = json_data[ "auto_arm_defer_time" ]

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._options = IntegraPartOptions.NONE

            opt1 = payload[ 20 ] if payload_len > 20 else 0x00
            if opt1 > 0:
                self._options |= IntegraPartOptions.TWO_CODES_TO_ARM if opt1 & (1 << 0) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.TWO_CODES_TO_DISARM if opt1 & (1 << 1) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.TIMER_PRIORITY if opt1 & (1 << 2) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.TWO_CODES_ON_TO_DEVICES if opt1 & (1 << 3) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.ALARM_VERIFICATION if opt1 & (1 << 4) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.EXIT_DELAY_CAN_BE_SHORTENED if opt1 & (1 << 5) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.INFINITE_EXIT_DELAY if opt1 & (1 << 6) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.CONST_1ST_CODE_VALIDITY_PERIOD if opt1 & (1 << 7) else IntegraPartOptions.NONE

            opt2 = payload[ 21 ] if payload_len > 21 else 0x00
            if opt2 > 0:
                self._options |= IntegraPartOptions.CONST_BLOCKING_TIME if opt2 & (1 << 0) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.DO_NOT_DISARM_IN_CASE_OF_ALARM if opt2 & (1 << 1) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.OPT_UNUSED2 if opt1 & (1 << 2) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.OPT_UNUSED3 if opt2 & (1 << 3) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.OPT_UNUSED4 if opt2 & (1 << 4) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.OPT_UNUSED5 if opt2 & (1 << 5) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.OPT_UNUSED6 if opt2 & (1 << 6) else IntegraPartOptions.NONE
                self._options |= IntegraPartOptions.AUTO_ARM_CAN_BE_DEFERRED if opt2 & (1 << 7) else IntegraPartOptions.NONE

            opt3 = ((payload[ 22 ] << 8) | payload[ 23 ]) if payload_len > 23 else 0x00
            if opt3 > 0:
                self._auto_arm_defer_status = IntegraAutoArmDeferStatus( opt3 & 0x0003 ) if (opt3 & 0x0003) in IntegraAutoArmDeferStatuses else IntegraAutoArmDeferStatus.INACTIVE
                self._auto_arm_defer_time = (opt3 & 0xFFFC) >> 2

    @property
    def options( self ):
        return self._options

    @property
    def auto_arm_defer_status( self ):
        return self._auto_arm_defer_status

    @property
    def auto_arm_defer_time( self ):
        return self._auto_arm_defer_time


class IntegraPartWithObjOptsDepsElement( IntegraPartWithObjOptsElement ):
    element_set = "parts"
    element_type = IntegraElementType.PARTITION_WITH_OBJ_OPTS_DEPS

    def __init__( self ):
        super().__init__()
        self._deps: list[ int ] = [ ]

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Deps": f"{self.deps}"
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "deps": self.deps,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._deps = json_data[ "deps" ]

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._deps = IntegraHelper.parts_from_bytes( payload[ 24:29 ] ) if payload_len > 27 else [ ]

    @property
    def deps( self ) -> list[ int ]:
        return self._deps


class IntegraZoneReactionType( IntEnum ):
    ENTRY_EXIT__0 = 0  # Wejścia / Wyjścia
    ENTRY__1 = 1  # Wejściowa
    DELAYED_WITH_SIGNAL__2 = 2  # Opóżniona z sygn.
    DELAYED_INTERIOR__3 = 3  # Opóźniona wewnętrzna
    PERIMETER__4 = 4  # Obwodowa
    INSTANT__5 = 5  # Zwykła
    EXIT__6 = 6  # Wyjściowa
    DAY_NIGHT__7 = 7  # Cicha / Głośna
    EXTERIOR__8 = 8  # Zewnętrzna
    TAMPER_24H__9 = 9  # 24h sabotażowa
    VIBRATION_24H__10 = 10  # 24h wibracyjna
    CASH_MACHINE_24H__11 = 11  # 24h bankomatowa
    PANIC_AUDIBLE__12 = 12  # Napadowa głośna
    PANIC_SILENT__13 = 13  # Napadowa cicha
    MEDICAL_BUTTON__14 = 14  # Medyczna przycisk
    PERSONAL_EMERGENCY__15 = 15  # Medyczna pilot
    COUNTING_L1__16 = 16  # Licznikowa L1
    COUNTING_L2__17 = 17  # Licznikowa L2
    COUNTING_L3__18 = 18  # Licznikowa L3
    COUNTING_L4__19 = 19  # Licznikowa L4
    COUNTING_L5__20 = 20  # Licznikowa L5
    COUNTING_L6__21 = 21  # Licznikowa L6
    COUNTING_L7__22 = 22  # Licznikowa L7
    COUNTING_L8__23 = 23  # Licznikowa L8
    COUNTING_L9__24 = 24  # Licznikowa L9
    COUNTING_L10__25 = 25  # Licznikowa L10
    COUNTING_L11__26 = 26  # Licznikowa L11
    COUNTING_L12__27 = 27  # Licznikowa L12
    COUNTING_L13__28 = 28  # Licznikowa L13
    COUNTING_L14__29 = 29  # Licznikowa L14
    COUNTING_L15__30 = 30  # Licznikowa L15
    COUNTING_L16__31 = 31  # Licznikowa L16
    FIRE_24H__32 = 32  # 24h pożarowa
    FIRE_24H_SMOKE__33 = 33  # 24h pożarowa - czujka dymu
    FIRE_24H_COMBUSTION__34 = 34  # 24h pożarowa - czujka spalenia
    FIRE_24H_WATER_FLOW__35 = 35  # 24h pożarowa - czujka wody
    FIRE_24H_HEAT__36 = 36  # 24h pożarowa - czujnik temperatury
    FIRE_24H_PULL_STATION__37 = 37  # 24h pożarowa - przycisk
    FIRE_24H_DUCT__38 = 38  # 24h pożarowa - DUCT
    FIRE_24H_FLAME__39 = 39  # 24h pożarowa - czujnik płomienia
    FIRE_24H_SUPERVISORY__40 = 40  # 24h pożarowa - zabezmienie obw. PPOż
    FIRE_24H_LOW_WATER_PRESSURE__41 = 41  # 24h pożarowa - czujnik ciśnienia wody
    FIRE_24H_LOW_CO2__42 = 42  # 24h pożarowa - czujnik ciśnienia CO2
    FIRE_24H_WATER_VALVE_DETECTOR__43 = 43  # 24h pożarowa - czujnik zaworu
    FIRE_24H_LOW_WATER_LEVEL__44 = 44  # 24h pożarowa - czujnik poziomu wody
    FIRE_24H_PUMP_ACTIVATED__45 = 45  # 24h pożarowa - załączenie pomp
    FIRE_24H_PUMP_FAILURE__46 = 46  # 24h pożarowa - awaria pomp
    NO_ALARM_ACTION__47 = 47  # Bez akcji alarmowej
    AUX_24H_PROTECTION_LOOP__48 = 48  # 24h pom. - ogólna
    AUX_24H_GAS_DETECTOR__49 = 49  # 24h pom. - czujnik gazu
    AUX_24H_REFRIGERATION__50 = 50  # 24h pom. - zamarzanie
    AUX_24H_LOSE_OF_HEAT__51 = 51  # 24h pom. - utrata ogrzewania
    AUX_24H_WATER_LEAK__52 = 52  # 24h pom. - wyciek wody
    AUX_24H_FOIL_BREAK__53 = 53  # 24h pom. - zabezpieczenie (nie włamaniowe)
    AUX_24H_LOW_GAS_PRESSURE__54 = 54  # 24h pom. - niskie ciśnienie gazu w butli
    AUX_24H_HIGH_TEMP__55 = 55  # 24h pom. - zbyt wysoka temperatura
    AUX_24H_LOW_TEMP__56 = 56  # 24h pom. - zbyt niska temperatura
    TECH_DOOR_OPEN__57 = 57  # Techniczna - kontrola drzwi
    TECH_DOOR_BUTTON__58 = 58  # Techniczna - przycisk drzwi
    TECH_TROUBLES_AC_LOSE__59 = 59  # Techniczna - awaria AC
    TECH_TROUBLES_BATT_LOW__60 = 60  # Techniczna - awaria AKU
    TECH_TROUBLES_GSM_LINK__61 = 61  # Techniczna - awaria GSM
    TECH_PWR_OVERLOAD__62 = 62  # Techniczna - przeciązenie zasilania
    TROUBLES_LOCAL__63 = 63  # Awaria (lokalna)
    BYPASSING_GROUP1__64 = 64  # Blokująca grupę 1
    BYPASSING_GROUP2__65 = 65  # Blokująca grupę 2
    BYPASSING_GROUP3__66 = 66  # Blokująca grupę 3
    BYPASSING_GROUP4__67 = 67  # Blokująca grupę 4
    BYPASSING_GROUP5__68 = 68  # Blokująca grupę 5
    BYPASSING_GROUP6__69 = 69  # Blokująca grupę 6
    BYPASSING_GROUP7__70 = 70  # Blokująca grupę 7
    BYPASSING_GROUP8__71 = 71  # Blokująca grupę 8
    BYPASSING_GROUP9__72 = 72  # Blokująca grupę 9
    BYPASSING_GROUP10__73 = 73  # Blokująca grupę 10
    BYPASSING_GROUP11__74 = 74  # Blokująca grupę 11
    BYPASSING_GROUP12__75 = 75  # Blokująca grupę 12
    BYPASSING_GROUP13__76 = 76  # Blokująca grupę 13
    BYPASSING_GROUP14__77 = 77  # Blokująca grupę 14
    BYPASSING_GROUP15__78 = 78  # Blokująca grupę 15
    BYPASSING_GROUP16__79 = 79  # Blokująca grupę 16
    ARMING__80 = 80  # Załączenie czuwania
    DISARMING__81 = 81  # Wyłącznie czuwania
    ARM_DISARM__82 = 82  # Załącznie / Wyłączenie czuwania
    CLEARING_ALARM__83 = 83  # Kasująca alarm
    GUARD__84 = 84  # Wartownicza
    ENTRY_EXIT_CONDITIONAL__85 = 85  # Wejścia / Wyjścia warunkowa
    ENTRY_EXIT_FINAL__86 = 86  # Wejścia / Wyjścia finalna
    EXIT_FINAL__87 = 87  # Wyjścia finalna
    BURGLARY_24H__88 = 88  # 24h włamaniowa
    FINISHING_EXIT_DELAY__89 = 89  # Kończąca czas na wyjście
    DISABLING_VERIFICATION__90 = 90  # Blokująca weryfikację
    MASKING_DETECTOR__91 = 91  # Czujnik maskowania
    OUTPUTS_GROUP_OFF__92 = 92  # Wył. grupę wyjść
    OUTPUTS_GROUP_ON__93 = 93  # Zał. grupę wyjść
    ENTRY_EXIT_INTERIOR__94 = 94  # Wejścia / Wyjścia wewnętrzna
    ENTRY_INTERIOR__95 = 95  # Wejściowa wewnętrzna
    FIRE_MONITORING__96 = 96  # Monitorująca pożarowa
    FIRE_PANEL_FAULT_MONITORING__97 = 97  # Monitorująca - uszkodzenie centrali ppoż
    FUTURE_USE__98 = 98
    FUTURE_USE__99 = 99
    FUTURE_USE__100 = 100
    FUTURE_USE__101 = 101
    FUTURE_USE__102 = 102
    FUTURE_USE__103 = 103
    FUTURE_USE__104 = 104
    FUTURE_USE__105 = 105
    FUTURE_USE__106 = 106
    FUTURE_USE__107 = 107
    FUTURE_USE__108 = 108
    FUTURE_USE__109 = 109
    FUTURE_USE__110 = 110
    FUTURE_USE__111 = 111
    FUTURE_USE__112 = 112
    FUTURE_USE__113 = 113
    FUTURE_USE__114 = 114
    FUTURE_USE__115 = 115
    FUTURE_USE__116 = 116
    FUTURE_USE__117 = 117
    FUTURE_USE__118 = 118
    FUTURE_USE__119 = 119
    FUTURE_USE__120 = 120
    FUTURE_USE__121 = 121
    FUTURE_USE__122 = 122
    FUTURE_USE__123 = 123
    FUTURE_USE__124 = 124
    FUTURE_USE__125 = 125
    FUTURE_USE__126 = 126
    FUTURE_USE__127 = 127
    FUTURE_USE__128 = 128
    FUTURE_USE__129 = 129
    FUTURE_USE__130 = 130
    FUTURE_USE__131 = 131
    FUTURE_USE__132 = 132
    FUTURE_USE__133 = 133
    FUTURE_USE__134 = 134
    FUTURE_USE__135 = 135
    FUTURE_USE__136 = 136
    FUTURE_USE__137 = 137
    FUTURE_USE__138 = 138
    FUTURE_USE__139 = 139
    FUTURE_USE__140 = 140
    FUTURE_USE__141 = 141
    FUTURE_USE__142 = 142
    FUTURE_USE__143 = 143
    FUTURE_USE__144 = 144
    FUTURE_USE__145 = 145
    FUTURE_USE__146 = 146
    FUTURE_USE__147 = 147
    FUTURE_USE__148 = 148
    FUTURE_USE__149 = 149
    FUTURE_USE__150 = 150
    FUTURE_USE__151 = 151
    FUTURE_USE__152 = 152
    FUTURE_USE__153 = 153
    FUTURE_USE__154 = 154
    FUTURE_USE__155 = 155
    FUTURE_USE__156 = 156
    FUTURE_USE__157 = 157
    FUTURE_USE__158 = 158
    FUTURE_USE__159 = 159
    FUTURE_USE__160 = 160
    FUTURE_USE__161 = 161
    FUTURE_USE__162 = 162
    FUTURE_USE__163 = 163
    FUTURE_USE__164 = 164
    FUTURE_USE__165 = 165
    FUTURE_USE__166 = 166
    FUTURE_USE__167 = 167
    FUTURE_USE__168 = 168
    FUTURE_USE__169 = 169
    FUTURE_USE__170 = 170
    FUTURE_USE__171 = 171
    FUTURE_USE__172 = 172
    FUTURE_USE__173 = 173
    FUTURE_USE__174 = 174
    FUTURE_USE__175 = 175
    FUTURE_USE__176 = 176
    FUTURE_USE__177 = 177
    FUTURE_USE__178 = 178
    FUTURE_USE__179 = 179
    FUTURE_USE__180 = 180
    FUTURE_USE__181 = 181
    FUTURE_USE__182 = 182
    FUTURE_USE__183 = 183
    FUTURE_USE__184 = 184
    FUTURE_USE__185 = 185
    FUTURE_USE__186 = 186
    FUTURE_USE__187 = 187
    FUTURE_USE__188 = 188
    FUTURE_USE__189 = 189
    FUTURE_USE__190 = 190
    FUTURE_USE__191 = 191
    FUTURE_USE__192 = 192
    FUTURE_USE__193 = 193
    FUTURE_USE__194 = 194
    FUTURE_USE__195 = 195
    FUTURE_USE__196 = 196
    FUTURE_USE__197 = 197
    FUTURE_USE__198 = 198
    FUTURE_USE__199 = 199
    FUTURE_USE__200 = 200
    FUTURE_USE__201 = 201
    FUTURE_USE__202 = 202
    FUTURE_USE__203 = 203
    FUTURE_USE__204 = 204
    FUTURE_USE__205 = 205
    FUTURE_USE__206 = 206
    FUTURE_USE__207 = 207
    FUTURE_USE__208 = 208
    FUTURE_USE__209 = 209
    FUTURE_USE__210 = 210
    FUTURE_USE__211 = 211
    FUTURE_USE__212 = 212
    FUTURE_USE__213 = 213
    FUTURE_USE__214 = 214
    FUTURE_USE__215 = 215
    FUTURE_USE__216 = 216
    FUTURE_USE__217 = 217
    FUTURE_USE__218 = 218
    FUTURE_USE__219 = 219
    FUTURE_USE__220 = 220
    FUTURE_USE__221 = 221
    FUTURE_USE__222 = 222
    FUTURE_USE__223 = 223
    FUTURE_USE__224 = 224
    FUTURE_USE__225 = 225
    FUTURE_USE__226 = 226
    FUTURE_USE__227 = 227
    FUTURE_USE__228 = 228
    FUTURE_USE__229 = 229
    FUTURE_USE__230 = 230
    FUTURE_USE__231 = 231
    FUTURE_USE__232 = 232
    FUTURE_USE__233 = 233
    FUTURE_USE__234 = 234
    FUTURE_USE__235 = 235
    FUTURE_USE__236 = 236
    FUTURE_USE__237 = 237
    FUTURE_USE__238 = 238
    FUTURE_USE__239 = 239
    FUTURE_USE__240 = 240
    FUTURE_USE__241 = 241
    FUTURE_USE__242 = 242
    FUTURE_USE__243 = 243
    FUTURE_USE__244 = 244
    FUTURE_USE__245 = 245
    FUTURE_USE__246 = 246
    FUTURE_USE__247 = 247
    FUTURE_USE__248 = 248
    FUTURE_USE__249 = 249
    FUTURE_USE__250 = 250
    FUTURE_USE__251 = 251
    FUTURE_USE__252 = 252
    FUTURE_USE__253 = 253
    FUTURE_USE__254 = 254
    FUTURE_USE__255 = 255
    ANY = 256

IntegraZoneReactionTypes = [ item.value for item in IntegraZoneReactionType ]


class IntegraZoneElement( IntegraElement ):
    element_set = "zones"
    element_type = IntegraElementType.ZONE

    def __init__( self ):
        super().__init__()
        self._reaction_type: IntegraZoneReactionType = IntegraZoneReactionType.INSTANT__5

    @property
    def element_id( self ):
        return self.element_no if self.element_no < 256 else 0

    @property
    def zone_no( self ) -> int:
        return self.element_no

    @property
    def reaction_type( self ) -> IntegraZoneReactionType:
        return self._reaction_type

    def _set_reaction_type( self, value: int ):
        self._reaction_type = IntegraZoneReactionType( value & 0xFF ) if value in IntegraZoneReactionTypes else IntegraZoneReactionType.INSTANT__5

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ZoneNo": f"{self.zone_no}",
            "ReactionType": f"{self.reaction_type.name}",
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "reaction_type": self._reaction_type,
            "reaction_name": self._reaction_type.name
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._set_reaction_type( json_data.get( "reaction_type", -1 ) )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._set_reaction_type( payload[ 2 ] if payload_len > 2 else 0xFF )


class IntegraZoneWithPartsElement( IntegraZoneElement ):
    element_set = "zones"
    element_type = IntegraElementType.ZONE_WITH_PARTS

    def __init__( self ):
        super().__init__()
        self._zone_type: int = 0xFF
        self._part_no: int = 0x00

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "PartNo": f"{self.part_no}",
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "part_no": self.part_no,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._part_no = json_data[ "part_no" ]

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._part_no = payload[ 19 ] if payload_len > 19 else 0x00

    @property
    def part_no( self ) -> int:
        return self._part_no


class IntegraOutputElementType( IntEnum ):
    UNUSED__0 = 0  # Niewykorzystane
    ALARM_BURGLARY__1 = 1  # Alarm włamaniaowy
    ALARM_FIRE_BURGLARY__2 = 2  # Alarm pożarowy / włamaniowy
    ALARM_FIRE__3 = 3  # Alarm pożarowy
    ALARM_KEYPAD__4 = 4  # Alarm z klawiatury
    ALARM_FIRE_KEYPAD__5 = 5  # Alarm pożarowy klawiatura
    ALARM_PANIC_KEYPAD__6 = 6  # Alarm napadowy klawiatura
    ALARM_MEDICAL_KEYPAD__7 = 7  # Alarm medyczny klawiatura
    ALARM_TAMPER__8 = 8  # Alarm sabotażowy
    ALARM_DAY__9 = 9  # Alarm DAY
    ALARM_DURESS__10 = 10  # Alarm "PRZYMUS"
    CHIME__11 = 11  # Gong
    ALARM_SILENT__12 = 12  # Cichy alarm
    ALARM_TECHNICAL__13 = 13  # Alarm techniczny
    ZONE_VIOLATION__14 = 14  # Naruszenie wejścia
    VIDEO_ON_DISARMED__15 = 15  # Wideo bez zuwania
    VIDEO_ON_ARMED__16 = 16  # Wideo w czuwaniu
    STATUS_READY__17 = 17  # Wskaźnik GOTOWY
    STATUS_BYPASS__18 = 18  # Wskaźnik BLOKOWAŃ
    STATUS_EXIT_DELAY__19 = 19  # Wskaźnik czasu na wyjście
    STATUS_ENTRY_DELAY__20 = 20  # Wskaźnik czasu na wejście
    STATUS_ARMED__21 = 21  # Wskaźnik czuwania
    STATUS_FULL_ARMED__22 = 22  # Wskaźnik czuwania wszystkiego
    BEEP_ARM_DISARM__23 = 23  # Potwierdzenie załączenia / wyłączenia
    SWITCH_MONO__24 = 24  # Przełącznik MONO
    SWITCH_BI__25 = 25  # Przełącznik BI
    TIMER__26 = 26  # Timer
    STATUS_TROUBLE__27 = 27  # Wskaźnik awarii
    TROUBLE_AC_LOSS_MAINBOARD__28 = 28  # Awaria zasialania AC płyty gł.
    TROUBLE_AC_LOSS_TECH_ZONE__29 = 29  # Awaria zasialania AC z wejść
    TROUBLE_AC_LOSS_EXP_MODULE__30 = 30  # Awaria zasialania AC ekspandery
    TROUBLE_BATT_MAINBOARD__31 = 31  # Awaria AKU płyty gł.
    TROUBLE_BATT_TECH_ZONE__32 = 32  # Awaria AKU z wejść
    TROUBLE_BATT_EXP_MODULE__33 = 33  # Awaria AKU ekspandery
    TROUBLE_DETECTOR__34 = 34  # Awaria wejścia
    STATUS_PHONE_LINE_IN_USE__35 = 35  # Wskaźnik telefonowania
    GROUND_START__36 = 36  # Ground Start
    REPORTING_ACK__37 = 37  # Potwierdzenie monitorowania
    STATUS_SERVICE_MODE__38 = 38  # Wskaźnik trybu serwisowego
    TEST_VIBRATION_DETECTORS__39 = 39  # Test czujek wibracyjnych
    STATUS_CASH_MACHINE_BYPASS__40 = 40  # Wskaźnik blok. bankomat.
    POWER_SUPPLY__41 = 41  # Zasilanie
    POWER_SUPPLY_ON_ARMED__42 = 42  # Zasilanie w czuwaniu
    RESETABLE_POWER_SUPPLY__43 = 43  # Zasilanie z resetem
    FIRE_DETECTORS_POWER_SUPPLY__44 = 44  # Zasilanie czujek pożarowych
    STATUS_PARTITION_BLOCK__45 = 45  # Wskaźnik blokady strefy
    OUTPUTS_LOGICAL_AND__46 = 46  # Iloczyn logiczny wyjść
    OUTPUTS_LOGICAL_OR__47 = 47  # Suma logiczna wyjść
    VOICE_MESSAGE0__48 = 48  # Syntezer 0
    VOICE_MESSAGE1__49 = 49  # Syntezer 1
    VOICE_MESSAGE2__50 = 50  # Syntezer 2
    VOICE_MESSAGE3__51 = 51  # Syntezer 3
    VOICE_MESSAGE4__52 = 52  # Syntezer 4
    VOICE_MESSAGE5__53 = 53  # Syntezer 5
    VOICE_MESSAGE6__54 = 54  # Syntezer 6
    VOICE_MESSAGE7__55 = 55  # Syntezer 7
    VOICE_MESSAGE8__56 = 56  # Syntezer 8
    VOICE_MESSAGE9__57 = 57  # Syntezer 9
    VOICE_MESSAGE10__58 = 58  # Syntezer 10
    VOICE_MESSAGE11__59 = 59  # Syntezer 11
    VOICE_MESSAGE12__60 = 60  # Syntezer 12
    VOICE_MESSAGE13__61 = 61  # Syntezer 13
    VOICE_MESSAGE14__62 = 62  # Syntezer 14
    VOICE_MESSAGE15__63 = 63  # Syntezer 15
    REMOTE_SWITCH1__64 = 64  # Przekaźnik tel. 1
    REMOTE_SWITCH2__65 = 65  # Przekaźnik tel. 2
    REMOTE_SWITCH3__66 = 66  # Przekaźnik tel. 3
    REMOTE_SWITCH4__67 = 67  # Przekaźnik tel. 4
    REMOTE_SWITCH5__68 = 68  # Przekaźnik tel. 5
    REMOTE_SWITCH6__69 = 69  # Przekaźnik tel. 6
    REMOTE_SWITCH7__70 = 70  # Przekaźnik tel. 7
    REMOTE_SWITCH8__71 = 71  # Przekaźnik tel. 8
    REMOTE_SWITCH9__72 = 72  # Przekaźnik tel. 9
    REMOTE_SWITCH10__73 = 73  # Przekaźnik tel. 10
    REMOTE_SWITCH11__74 = 74  # Przekaźnik tel. 11
    REMOTE_SWITCH12__75 = 75  # Przekaźnik tel. 12
    REMOTE_SWITCH13__76 = 76  # Przekaźnik tel. 13
    REMOTE_SWITCH14__77 = 77  # Przekaźnik tel. 14
    REMOTE_SWITCH15__78 = 78  # Przekaźnik tel. 15
    REMOTE_SWITCH16__79 = 79  # Przekaźnik tel. 16
    NO_GRUAR_TOUR__80 = 80  # Brak obchodu wartownika
    TROUBLE_AC_LOSE_LONG_MAINBOARD__81 = 81  # Długa awaria AC płyty gł.
    TROUBLE_AC_LOSE_LONG_EXP_MODULE__82 = 82  # Długa awaria AC modułów
    OUTPUTS_OFF__83 = 83  # Koniec sygnalizacji wyjść
    ACCESS_CODE_ENTERING__84 = 84  # Sygnalizacja podania hasł
    USE_OF_ACCESS_CODE__85 = 85  # Sygnalizacja użycia hasł
    DOOR_OPEN_INDICATOR__86 = 86  # Wskaźnik otwartych drzwi
    DOOR_OPEN_LONG_INDICATOR__87 = 87  # Wskaźnik długo otwrtych drzwi
    ALARM_BURGLARY__88 = 88  # Alarm włamaniowy (bez sabotaży i ppoż)
    LOG_MEM_FILLED50__89 = 89  # 50% pamięci zdarzeń zapełnione
    LOG_MEM_FILLED90__90 = 90  # 90% pamięci zdarzeń zapełnione
    AUTO_ARM_DELAY_START__91 = 91  # Sygnnalizacja odliczania autouzbrojenia stref
    STATUS_AUTO_ARM_DELAY__92 = 92  # Wskaźnik odliczania autouzbrojenia stref
    UNAUTHORIZED_ACCESS__93 = 93  # Otwarcie drzwi bez autoryzacji
    ALARM_UNAUTHORIZED_ACCESS__94 = 94  # Alarm nieautoryzowany dostęp
    TROUBLE_IP_REPORTING__95 = 95  # Awaria monitoringu IP
    TROUBLE_PHONE_LINE__96 = 96  # Awarie GSM
    VOICE_MESSAGE__97 = 97  # Syntezer
    REMOTE_SWITCH__98 = 98  # Przekaźnik tel.
    ACCESS_CARD_READ__99 = 99  # Wczytano kartę
    CARD_HOLD_DOWN__100 = 100  # Przytrzymano kartę
    CARD_READ_EXPANDER__101 = 101  # Wczytano kartę na module
    TROUBLE_LINK_WIRELESS_ZONE__102 = 102  # Brak łączności - wejście bezprzewodowe
    TROUBLE_LINK_WIRELESS_OUTPUT__103 = 103  # Brak łączności - wyjście bezprzewodowe
    TROUBLE_LOW_BATT_WIRELESS_DEVICE__104 = 104  # Awaria baterii - urządzenie bezprzewodowe
    SHUTTER_UP__105 = 105  # Roleta w górę
    SHUTTER_DOWN__106 = 106  # Roleta w dół
    CARD_ON_READER_A__107 = 107  # Karta na głowicy A ekspandera
    CARD_ON_READER_B__108 = 108  # Karta na głowicy B ekspandera
    ZONES_LOGICAL_AND__109 = 109  # Iloczyn logiczny wejść
    ALARM_NOT_VERIFIED__110 = 110  # Alarm niezweryfikowany
    ALARM_VERIFIED__111 = 111  # Alarm zweryfikowany
    NO_ALARM_VERIFIED__112 = 112  # Weryfikacja - bez alarmu
    STATUS_VERIFICATION_DISABLED__113 = 113  # Wskażnik blokady weryfikacji
    STATUS_ZONE_TEST__114 = 114  # Wskażnik testu wejść
    STATUS_ARMING_TYPE__115 = 115  # Wskażnik typu czuwania
    INTERNAL_SIREN__116 = 116  # Sygnalizator wewnętrzny
    STATUS_TAMPERING__117 = 117  # Wskaźnik sabotażu
    KEYFOB_BATT_LOW__118 = 118  # Awaria baterii pilotów
    WIRELESS_SYSTEM_JAMMING__119 = 119  # Zagłuszanie modułu bezprzeowodowego
    THERMOSTAT__120 = 120  # Termostat
    MASKING__121 = 121  # Maskowanie czujki
    STATUS_MASKING__122 = 122  # Wskaźnik maskowania czujki
    FUTURE_USE__123 = 123
    FUTURE_USE__124 = 124
    FUTURE_USE__125 = 125
    FUTURE_USE__126 = 126
    FUTURE_USE__127 = 127
    FUTURE_USE__128 = 128
    FUTURE_USE__129 = 129
    FUTURE_USE__130 = 130
    FUTURE_USE__131 = 131
    FUTURE_USE__132 = 132
    FUTURE_USE__133 = 133
    FUTURE_USE__134 = 134
    FUTURE_USE__135 = 135
    FUTURE_USE__136 = 136
    FUTURE_USE__137 = 137
    FUTURE_USE__138 = 138
    FUTURE_USE__139 = 139
    FUTURE_USE__140 = 140
    FUTURE_USE__141 = 141
    FUTURE_USE__142 = 142
    FUTURE_USE__143 = 143
    FUTURE_USE__144 = 144
    FUTURE_USE__145 = 145
    FUTURE_USE__146 = 146
    FUTURE_USE__147 = 147
    FUTURE_USE__148 = 148
    FUTURE_USE__149 = 149
    FUTURE_USE__150 = 150
    FUTURE_USE__151 = 151
    FUTURE_USE__152 = 152
    FUTURE_USE__153 = 153
    FUTURE_USE__154 = 154
    FUTURE_USE__155 = 155
    FUTURE_USE__156 = 156
    FUTURE_USE__157 = 157
    FUTURE_USE__158 = 158
    FUTURE_USE__159 = 159
    FUTURE_USE__160 = 160
    FUTURE_USE__161 = 161
    FUTURE_USE__162 = 162
    FUTURE_USE__163 = 163
    FUTURE_USE__164 = 164
    FUTURE_USE__165 = 165
    FUTURE_USE__166 = 166
    FUTURE_USE__167 = 167
    FUTURE_USE__168 = 168
    FUTURE_USE__169 = 169
    FUTURE_USE__170 = 170
    FUTURE_USE__171 = 171
    FUTURE_USE__172 = 172
    FUTURE_USE__173 = 173
    FUTURE_USE__174 = 174
    FUTURE_USE__175 = 175
    FUTURE_USE__176 = 176
    FUTURE_USE__177 = 177
    FUTURE_USE__178 = 178
    FUTURE_USE__179 = 179
    FUTURE_USE__180 = 180
    FUTURE_USE__181 = 181
    FUTURE_USE__182 = 182
    FUTURE_USE__183 = 183
    FUTURE_USE__184 = 184
    FUTURE_USE__185 = 185
    FUTURE_USE__186 = 186
    FUTURE_USE__187 = 187
    FUTURE_USE__188 = 188
    FUTURE_USE__189 = 189
    FUTURE_USE__190 = 190
    FUTURE_USE__191 = 191
    FUTURE_USE__192 = 192
    FUTURE_USE__193 = 193
    FUTURE_USE__194 = 194
    FUTURE_USE__195 = 195
    FUTURE_USE__196 = 196
    FUTURE_USE__197 = 197
    FUTURE_USE__198 = 198
    FUTURE_USE__199 = 199
    FUTURE_USE__200 = 200
    FUTURE_USE__201 = 201
    FUTURE_USE__202 = 202
    FUTURE_USE__203 = 203
    FUTURE_USE__204 = 204
    FUTURE_USE__205 = 205
    FUTURE_USE__206 = 206
    FUTURE_USE__207 = 207
    FUTURE_USE__208 = 208
    FUTURE_USE__209 = 209
    FUTURE_USE__210 = 210
    FUTURE_USE__211 = 211
    FUTURE_USE__212 = 212
    FUTURE_USE__213 = 213
    FUTURE_USE__214 = 214
    FUTURE_USE__215 = 215
    FUTURE_USE__216 = 216
    FUTURE_USE__217 = 217
    FUTURE_USE__218 = 218
    FUTURE_USE__219 = 219
    FUTURE_USE__220 = 220
    FUTURE_USE__221 = 221
    FUTURE_USE__222 = 222
    FUTURE_USE__223 = 223
    FUTURE_USE__224 = 224
    FUTURE_USE__225 = 225
    FUTURE_USE__226 = 226
    FUTURE_USE__227 = 227
    FUTURE_USE__228 = 228
    FUTURE_USE__229 = 229
    FUTURE_USE__230 = 230
    FUTURE_USE__231 = 231
    FUTURE_USE__232 = 232
    FUTURE_USE__233 = 233
    FUTURE_USE__234 = 234
    FUTURE_USE__235 = 235
    FUTURE_USE__236 = 236
    FUTURE_USE__237 = 237
    FUTURE_USE__238 = 238
    FUTURE_USE__239 = 239
    FUTURE_USE__240 = 240
    FUTURE_USE__241 = 241
    FUTURE_USE__242 = 242
    FUTURE_USE__243 = 243
    FUTURE_USE__244 = 244
    FUTURE_USE__245 = 245
    FUTURE_USE__246 = 246
    FUTURE_USE__247 = 247
    FUTURE_USE__248 = 248
    FUTURE_USE__249 = 249
    FUTURE_USE__250 = 250
    FUTURE_USE__251 = 251
    FUTURE_USE__252 = 252
    FUTURE_USE__253 = 253
    FUTURE_USE__254 = 254
    FUTURE_USE__255 = 255


IntegraOutputElementSwitchable: list[IntegraOutputElementType] = [
    IntegraOutputElementType.SWITCH_MONO__24,
    IntegraOutputElementType.SWITCH_BI__25,
    IntegraOutputElementType.SHUTTER_UP__105,
    IntegraOutputElementType.SHUTTER_DOWN__106,
]

IntegraOutputElementTypes = [ item.value for item in IntegraOutputElementType ]


class IntegraOutputElement( IntegraElement ):
    element_set = "outputs"
    element_type = IntegraElementType.OUTPUT

    def __init__( self ):
        super().__init__()
        self._output_type: IntegraOutputElementType = IntegraOutputElementType.UNUSED__0

    @property
    def element_id( self ):
        return self.element_no if self.element_no < 256 else 0

    @property
    def output_no( self ) -> int:
        return self.element_no

    @property
    def output_type( self ) -> IntegraOutputElementType:
        return self._output_type

    def _set_output_type( self, value: int ):
        self._output_type = IntegraOutputElementType( value & 0xFF ) if (value & 0xFF) in IntegraOutputElementTypes else IntegraOutputElementType.UNUSED__0

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "OutputNo": f"{self.output_no}",
            "OutputType": f"{self.output_type.name}",
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._set_output_type( json_data.get( "output_type", self.output_type ) )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "output_type": self._output_type,
            "output_type_name": self._output_type.name,
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._set_output_type( payload[ 2 ] if payload_len > 2 else 0x00 )


class IntegraOutputWithDurationElement( IntegraOutputElement ):
    element_set = "outputs"
    element_type = IntegraElementType.OUTPUT_WITH_DURATION

    def __init__( self ):
        super().__init__()
        self._duration: float = 0.0

    @property
    def duration( self ) -> float:
        return self._duration

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Duration": f"{self.duration}",
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        self._duration = json_data.get( "duration", self.duration )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "duration": self._duration,
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._duration = float( ((payload[ 19 ] << 8) | payload[ 20 ]) / 10.0 ) if payload_len > 20 else 0.0


class IntegraUserElement( IntegraElement ):
    element_set = "users"
    element_type = IntegraElementType.USER

    def __init__( self ):
        super().__init__()
        self._serial_no: int = 0
        self._is_admin: bool = self.element_id > 0xF0

    @property
    def user_no( self ) -> int:
        return self.element_no

    @property
    def serial_no( self ) -> int:
        return self._serial_no

    @property
    def is_admin( self ) -> bool:
        return self._is_admin

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserNo": f"{self.user_no}",
            "IsAdmin": f"{self.is_admin}",
            "SerialNo": f"0x{self.serial_no:02X}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._serial_no = payload[ 19 ] if payload_len > 19 else 0xFF


class IntegraAdminElement( IntegraUserElement ):
    element_set = "admins"
    element_type = IntegraElementType.USER

    def __init__( self ):
        super().__init__()

    @property
    def element_id( self ) -> int:
        return self.element_no + 0xF0

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            if self._element_no > 0xF0:
                self._element_no -= 0xF0


class IntegraExpanderElement( IntegraElement ):
    element_set = "expanders"
    element_type = IntegraElementType.EXPANDER

    def __init__( self ):
        super().__init__()
        self._expander_type: IntegraExpanderType = IntegraExpanderType.UNKNOWN

    @property
    def element_id( self ) -> int:
        return self.expander_no + 0x80

    @property
    def expander_type( self ) -> IntegraExpanderType:
        return self._expander_type

    @property
    def expander_no( self ) -> int:
        return self.element_no

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ExpanderNo": f"{self.expander_no}",
            "ExpanderType": f"{self.expander_type.name}",
        } )

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "expander_type": self.expander_type.value,
            "expander_type_name": self.expander_type.name,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json(json_data)
        expander_type_value = json_data.get( "expander_type", -1 )
        self._expander_type = IntegraExpanderType( expander_type_value ) if expander_type_value in IntegraExpanderTypes else IntegraExpanderType.UNKNOWN

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._expander_type = IntegraExpanderType( payload[ 2 ] ) if payload_len > 2 and payload[ 2 ] in IntegraExpanderTypes else IntegraExpanderType.UNKNOWN
            if self._element_no > 0x80:
                self._element_no -= 0x80


class IntegraManipulatorElement( IntegraElement ):
    element_set = "manipulators"
    element_type = IntegraElementType.MANIPULATOR

    def __init__( self ):
        super().__init__()
        self._manipulator_type: IntegraManipulatorType = IntegraManipulatorType.UNKNOWN

    @property
    def element_id( self ) -> int:
        return self.manipulator_no + 0xC0

    @property
    def manipulator_type( self ) -> IntegraManipulatorType:
        return self._manipulator_type

    @property
    def manipulator_no( self ) -> int:
        return self.element_no

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ManipulatorNo": f"{self.manipulator_no}",
            "ManipulatorType": f"{self.manipulator_type.name}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if self.valid:
            self._manipulator_type = IntegraManipulatorType( payload[ 2 ] ) if payload_len > 2 and payload[ 2 ] in IntegraManipulatorTypes else IntegraManipulatorType.UNKNOWN
            if self._element_no > 0xC0:
                self._element_no -= 0xC0

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._write_json( json_data )
        json_data.update( {
            "manipulator_type": self.manipulator_type,
            "manipulator_type_name": self.manipulator_type.name,
        } )

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        super()._read_json( json_data )
        manipulator_type_value = json_data.get( "manipulator_type", -1 )
        self._manipulator_type = IntegraManipulatorType(manipulator_type_value) if manipulator_type_value in IntegraManipulatorTypes else IntegraManipulatorType.UNKNOWN


class IntegraTimerElement( IntegraElement ):
    element_set = "timers"
    element_type = IntegraElementType.TIMER

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "TimerNo": f"{self.timer_no}",
        } )

    def __init__( self ):
        super().__init__()

    @property
    def timer_no( self ) -> int:
        return self.element_no


class IntegraPhoneElement( IntegraElement ):
    element_set = "phones"
    element_type = IntegraElementType.TELEPHONE

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "PhoneNo": f"{self.phone_no}",
        } )

    def __init__( self ):
        super().__init__()

    @property
    def phone_no( self ) -> int:
        return self.element_no


class IntegraObjectElement( IntegraElement ):
    element_set = "objects"
    element_type = IntegraElementType.OBJECT

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ObjectNo": f"{self.object_no}",
        } )

    def __init__( self ):
        super().__init__()

    @property
    def object_no( self ) -> int:
        return self.element_no


for module_item in dir():
    if not module_item.startswith( "Integra" ):
        continue
    type_ = getattr( sys.modules[ __name__ ], module_item )
    try:
        if issubclass( type_, IntegraElement ):
            _LOGGER.debug( f"Registered {module_item}" )
            IntegraElementFactory.register_class( type_ )
    except TypeError:
        continue
# print("ElementFactoryRegister: Done!")