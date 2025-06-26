from enum import IntEnum, Flag

from .base import IntegraEntity, IntegraTypeVal
from .commands import IntegraCommand


class IntegraNotifySource( Flag ):
    NONE = 0x00
    PARTS = 0x01
    ZONES = 0x02
    OUTPUTS = 0x04
    DOORS = 0x08
    TROUBLES = 0x10
    TROUBLES_MEMORTY = 0x20
    DATA = 0x40
    OTHERS = 0x80


class IntegraNotifyEvent( IntEnum ):
    PARTS_ARMED_SUPPRESSED = 0x09
    PARTS_ARMED_REALLY = 0x0A
    PARTS_ARMED_MODE_2 = 0x0B
    PARTS_ARMED_MODE_3 = 0x0C
    PARTS_1ST_CODE_ENTERED = 0x0D
    PARTS_ENTRY_TIME = 0x0E
    PARTS_EXIT_TIME_ABOVE_10 = 0x0F
    PARTS_EXIT_TIME_BELOW_10 = 0x10
    PARTS_TEMP_BLOCKED = 0x11
    PARTS_BLOCKED_FOR_GUARD = 0x12
    PARTS_ALARM = 0x13
    PARTS_FIRE_ALARM = 0x14
    PARTS_ALARM_MEMORY = 0x15
    PARTS_FIRE_ALARM_MEMORY = 0x16
    PARTS_WITH_VIOLATED_ZONES = 0x25
    PARTS_WITH_VERIFIED_ALARMS = 0x27
    PARTS_ARMED_MODE_1 = 0x2A
    PARTS_WITH_WARNING_ALARMS = 0x2B

    ZONES_VIOLATION = 0x00
    ZONES_TAMPER = 0x01
    ZONES_ALARM = 0x02
    ZONES_TAMPER_ALARM = 0x03
    ZONES_ALARM_MEMORY = 0x04
    ZONES_TAMPER_ALARM_MEMORY = 0x05
    ZONES_BYPASS = 0x06
    ZONES_NO_VIOLATION_TROUBLE = 0x07
    ZONES_LONG_VIOLATION_TROUBLE = 0x08
    ZONES_ISOLATE = 0x26
    ZONES_MASKED = 0x28
    ZONES_MASKED_MEMORY = 0x29

    OUTPUTS_STATE = 0x17

    DOORS_OPENED = 0x18
    DOORS_OPENED_LONG = 0x19

    TROUBLES_PART1 = 0x1B
    TROUBLES_PART2 = 0x1C
    TROUBLES_PART3 = 0x1D
    TROUBLES_PART4 = 0x1E
    TROUBLES_PART5 = 0x1F
    TROUBLES_PART6 = 0x2C
    TROUBLES_PART7 = 0x2D
    TROUBLES_PART8 = 0x30

    TROUBLES_MEMORY_PART1 = 0x20
    TROUBLES_MEMORY_PART2 = 0x21
    TROUBLES_MEMORY_PART3 = 0x22
    TROUBLES_MEMORY_PART4 = 0x23
    TROUBLES_MEMORY_PART5 = 0x24
    TROUBLES_MEMORY_PART6 = 0x2E
    TROUBLES_MEMORY_PART7 = 0x2F
    TROUBLES_MEMORY_PART8 = 0x31

    RTC_AND_STATUS = 0x1A

    OUTPUT_POWER = 0x7B
    ZONE_TEMPERATURE = 0x7D

    __MAP_COMMAND_TO_EVENT: dict[ IntegraCommand, 'IntegraNotifyEvent' ] = {
        IntegraCommand.READ_ZONES_VIOLATION: ZONES_VIOLATION,
        IntegraCommand.READ_ZONES_TAMPER: ZONES_TAMPER,
        IntegraCommand.READ_ZONES_ALARM: ZONES_ALARM,
        IntegraCommand.READ_ZONES_TAMPER_ALARM: ZONES_TAMPER_ALARM,
        IntegraCommand.READ_ZONES_ALARM_MEMORY: ZONES_ALARM_MEMORY,
        IntegraCommand.READ_ZONES_TAMPER_ALARM_MEMORY: ZONES_TAMPER_ALARM_MEMORY,
        IntegraCommand.READ_ZONES_BYPASS: ZONES_BYPASS,
        IntegraCommand.READ_ZONES_NO_VIOLATION_TROUBLE: ZONES_NO_VIOLATION_TROUBLE,
        IntegraCommand.READ_ZONES_LONG_VIOLATION_TROUBLE: ZONES_LONG_VIOLATION_TROUBLE,
        IntegraCommand.READ_PARTS_ARMED_SUPPRESSED: PARTS_ARMED_SUPPRESSED,
        IntegraCommand.READ_PARTS_ARMED_REALLY: PARTS_ARMED_REALLY,
        IntegraCommand.READ_PARTS_ARMED_MODE_2: PARTS_ARMED_MODE_2,
        IntegraCommand.READ_PARTS_ARMED_MODE_3: PARTS_ARMED_MODE_3,
        IntegraCommand.READ_PARTS_1ST_CODE_ENTERED: PARTS_1ST_CODE_ENTERED,
        IntegraCommand.READ_PARTS_ENTRY_TIME: PARTS_ENTRY_TIME,
        IntegraCommand.READ_PARTS_EXIT_TIME_ABOVE_10: PARTS_EXIT_TIME_ABOVE_10,
        IntegraCommand.READ_PARTS_EXIT_TIME_BELOW_10: PARTS_EXIT_TIME_BELOW_10,
        IntegraCommand.READ_PARTS_TEMP_BLOCKED: PARTS_TEMP_BLOCKED,
        IntegraCommand.READ_PARTS_BLOCKED_FOR_GUARD: PARTS_BLOCKED_FOR_GUARD,
        IntegraCommand.READ_PARTS_ALARM: PARTS_ALARM,
        IntegraCommand.READ_PARTS_FIRE_ALARM: PARTS_FIRE_ALARM,
        IntegraCommand.READ_PARTS_ALARM_MEMORY: PARTS_ALARM_MEMORY,
        IntegraCommand.READ_PARTS_FIRE_ALARM_MEMORY: PARTS_FIRE_ALARM_MEMORY,
        IntegraCommand.READ_OUTPUTS_STATE: OUTPUTS_STATE,
        IntegraCommand.READ_DOORS_OPENED: DOORS_OPENED,
        IntegraCommand.READ_DOORS_OPENED_LONG: DOORS_OPENED_LONG,
        IntegraCommand.READ_RTC_AND_STATUS: RTC_AND_STATUS,
        IntegraCommand.READ_TROUBLES_PART1: TROUBLES_PART1,
        IntegraCommand.READ_TROUBLES_PART2: TROUBLES_PART2,
        IntegraCommand.READ_TROUBLES_PART3: TROUBLES_PART3,
        IntegraCommand.READ_TROUBLES_PART4: TROUBLES_PART4,
        IntegraCommand.READ_TROUBLES_PART5: TROUBLES_PART5,
        IntegraCommand.READ_TROUBLES_MEMORY_PART1: TROUBLES_MEMORY_PART1,
        IntegraCommand.READ_TROUBLES_MEMORY_PART2: TROUBLES_MEMORY_PART2,
        IntegraCommand.READ_TROUBLES_MEMORY_PART3: TROUBLES_MEMORY_PART3,
        IntegraCommand.READ_TROUBLES_MEMORY_PART4: TROUBLES_MEMORY_PART4,
        IntegraCommand.READ_TROUBLES_MEMORY_PART5: TROUBLES_MEMORY_PART5,
        IntegraCommand.READ_PARTS_WITH_VIOLATED_ZONES: PARTS_WITH_VIOLATED_ZONES,
        IntegraCommand.READ_ZONES_ISOLATE: ZONES_ISOLATE,
        IntegraCommand.READ_PARTS_WITH_VERIFIED_ALARMS: PARTS_WITH_VERIFIED_ALARMS,
        IntegraCommand.READ_ZONES_MASKED: ZONES_MASKED,
        IntegraCommand.READ_ZONES_MASKED_MEMORY: ZONES_MASKED_MEMORY,
        IntegraCommand.READ_PARTS_ARMED_MODE_1: PARTS_ARMED_MODE_1,
        IntegraCommand.READ_PARTS_WITH_WARNING_ALARMS: PARTS_WITH_WARNING_ALARMS,
        IntegraCommand.READ_TROUBLES_PART6: TROUBLES_PART6,
        IntegraCommand.READ_TROUBLES_PART7: TROUBLES_PART7,
        IntegraCommand.READ_TROUBLES_MEMORY_PART6: TROUBLES_MEMORY_PART6,
        IntegraCommand.READ_TROUBLES_MEMORY_PART7: TROUBLES_MEMORY_PART7,
        IntegraCommand.READ_TROUBLES_PART8: TROUBLES_PART8,
        IntegraCommand.READ_TROUBLES_MEMORY_PART8: TROUBLES_MEMORY_PART8,
        IntegraCommand.READ_OUTPUT_POWER: OUTPUT_POWER,
        IntegraCommand.READ_ZONE_TEMPERATURE: ZONE_TEMPERATURE
    }

    __MAP_EVENT_TO_COMMAND: dict[ 'IntegraNotifyEvent', IntegraCommand ] = {
        ZONES_VIOLATION: IntegraCommand.READ_ZONES_VIOLATION,
        ZONES_TAMPER: IntegraCommand.READ_ZONES_TAMPER,
        ZONES_ALARM: IntegraCommand.READ_ZONES_ALARM,
        ZONES_TAMPER_ALARM: IntegraCommand.READ_ZONES_TAMPER_ALARM,
        ZONES_ALARM_MEMORY: IntegraCommand.READ_ZONES_ALARM_MEMORY,
        ZONES_TAMPER_ALARM_MEMORY: IntegraCommand.READ_ZONES_TAMPER_ALARM_MEMORY,
        ZONES_BYPASS: IntegraCommand.READ_ZONES_BYPASS,
        ZONES_NO_VIOLATION_TROUBLE: IntegraCommand.READ_ZONES_NO_VIOLATION_TROUBLE,
        ZONES_LONG_VIOLATION_TROUBLE: IntegraCommand.READ_ZONES_LONG_VIOLATION_TROUBLE,
        PARTS_ARMED_SUPPRESSED: IntegraCommand.READ_PARTS_ARMED_SUPPRESSED,
        PARTS_ARMED_REALLY: IntegraCommand.READ_PARTS_ARMED_REALLY,
        PARTS_ARMED_MODE_2: IntegraCommand.READ_PARTS_ARMED_MODE_2,
        PARTS_ARMED_MODE_3: IntegraCommand.READ_PARTS_ARMED_MODE_3,
        PARTS_1ST_CODE_ENTERED: IntegraCommand.READ_PARTS_1ST_CODE_ENTERED,
        PARTS_ENTRY_TIME: IntegraCommand.READ_PARTS_ENTRY_TIME,
        PARTS_EXIT_TIME_ABOVE_10: IntegraCommand.READ_PARTS_EXIT_TIME_ABOVE_10,
        PARTS_EXIT_TIME_BELOW_10: IntegraCommand.READ_PARTS_EXIT_TIME_BELOW_10,
        PARTS_TEMP_BLOCKED: IntegraCommand.READ_PARTS_TEMP_BLOCKED,
        PARTS_BLOCKED_FOR_GUARD: IntegraCommand.READ_PARTS_BLOCKED_FOR_GUARD,
        PARTS_ALARM: IntegraCommand.READ_PARTS_ALARM,
        PARTS_FIRE_ALARM: IntegraCommand.READ_PARTS_FIRE_ALARM,
        PARTS_ALARM_MEMORY: IntegraCommand.READ_PARTS_ALARM_MEMORY,
        PARTS_FIRE_ALARM_MEMORY: IntegraCommand.READ_PARTS_FIRE_ALARM_MEMORY,
        OUTPUTS_STATE: IntegraCommand.READ_OUTPUTS_STATE,
        DOORS_OPENED: IntegraCommand.READ_DOORS_OPENED,
        DOORS_OPENED_LONG: IntegraCommand.READ_DOORS_OPENED_LONG,
        RTC_AND_STATUS: IntegraCommand.READ_RTC_AND_STATUS,
        TROUBLES_PART1: IntegraCommand.READ_TROUBLES_PART1,
        TROUBLES_PART2: IntegraCommand.READ_TROUBLES_PART2,
        TROUBLES_PART3: IntegraCommand.READ_TROUBLES_PART3,
        TROUBLES_PART4: IntegraCommand.READ_TROUBLES_PART4,
        TROUBLES_PART5: IntegraCommand.READ_TROUBLES_PART5,
        TROUBLES_MEMORY_PART1: IntegraCommand.READ_TROUBLES_MEMORY_PART1,
        TROUBLES_MEMORY_PART2: IntegraCommand.READ_TROUBLES_MEMORY_PART2,
        TROUBLES_MEMORY_PART3: IntegraCommand.READ_TROUBLES_MEMORY_PART3,
        TROUBLES_MEMORY_PART4: IntegraCommand.READ_TROUBLES_MEMORY_PART4,
        TROUBLES_MEMORY_PART5: IntegraCommand.READ_TROUBLES_MEMORY_PART5,
        PARTS_WITH_VIOLATED_ZONES: IntegraCommand.READ_PARTS_WITH_VIOLATED_ZONES,
        ZONES_ISOLATE: IntegraCommand.READ_ZONES_ISOLATE,
        PARTS_WITH_VERIFIED_ALARMS: IntegraCommand.READ_PARTS_WITH_VERIFIED_ALARMS,
        ZONES_MASKED: IntegraCommand.READ_ZONES_MASKED,
        ZONES_MASKED_MEMORY: IntegraCommand.READ_ZONES_MASKED_MEMORY,
        PARTS_ARMED_MODE_1: IntegraCommand.READ_PARTS_ARMED_MODE_1,
        PARTS_WITH_WARNING_ALARMS: IntegraCommand.READ_PARTS_WITH_WARNING_ALARMS,
        TROUBLES_PART6: IntegraCommand.READ_TROUBLES_PART6,
        TROUBLES_PART7: IntegraCommand.READ_TROUBLES_PART7,
        TROUBLES_MEMORY_PART6: IntegraCommand.READ_TROUBLES_MEMORY_PART6,
        TROUBLES_MEMORY_PART7: IntegraCommand.READ_TROUBLES_MEMORY_PART7,
        TROUBLES_PART8: IntegraCommand.READ_TROUBLES_PART8,
        TROUBLES_MEMORY_PART8: IntegraCommand.READ_TROUBLES_MEMORY_PART8,

        OUTPUT_POWER: IntegraCommand.READ_OUTPUT_POWER,
        ZONE_TEMPERATURE: IntegraCommand.READ_ZONE_TEMPERATURE,
    }

    @classmethod
    def from_command( cls, command: IntegraCommand ) -> 'IntegraNotifyEvent | None':
        if command in cls.__MAP_COMMAND_TO_EVENT:
            return cls( cls.__MAP_COMMAND_TO_EVENT[ command ] )
        return None

    @classmethod
    def to_commands( cls, notify_events: list[ 'IntegraNotifyEvent' ] | None ) -> list[ IntegraCommand ]:
        if notify_events is None:
            return [ ]
        result = [ ]
        for notify_event in notify_events:
            if notify_event in cls.__MAP_EVENT_TO_COMMAND:
                result.append( cls.__MAP_EVENT_TO_COMMAND[ notify_event ] )
        return result


IntegraPartsNotifyEvents = [
    IntegraNotifyEvent.PARTS_ARMED_SUPPRESSED,
    IntegraNotifyEvent.PARTS_ARMED_REALLY,
    IntegraNotifyEvent.PARTS_ARMED_MODE_2,
    IntegraNotifyEvent.PARTS_ARMED_MODE_3,
    IntegraNotifyEvent.PARTS_1ST_CODE_ENTERED,
    IntegraNotifyEvent.PARTS_ENTRY_TIME,
    IntegraNotifyEvent.PARTS_EXIT_TIME_ABOVE_10,
    IntegraNotifyEvent.PARTS_EXIT_TIME_BELOW_10,
    IntegraNotifyEvent.PARTS_TEMP_BLOCKED,
    IntegraNotifyEvent.PARTS_BLOCKED_FOR_GUARD,
    IntegraNotifyEvent.PARTS_ALARM,
    IntegraNotifyEvent.PARTS_FIRE_ALARM,
    IntegraNotifyEvent.PARTS_ALARM_MEMORY,
    IntegraNotifyEvent.PARTS_FIRE_ALARM_MEMORY,
    IntegraNotifyEvent.PARTS_WITH_VIOLATED_ZONES,
    IntegraNotifyEvent.PARTS_WITH_VERIFIED_ALARMS,
    IntegraNotifyEvent.PARTS_ARMED_MODE_1,
    IntegraNotifyEvent.PARTS_WITH_WARNING_ALARMS
]

IntegraZonesNotifyEvents = [
    IntegraNotifyEvent.ZONES_VIOLATION,
    IntegraNotifyEvent.ZONES_TAMPER,
    IntegraNotifyEvent.ZONES_ALARM,
    IntegraNotifyEvent.ZONES_TAMPER_ALARM,
    IntegraNotifyEvent.ZONES_ALARM_MEMORY,
    IntegraNotifyEvent.ZONES_TAMPER_ALARM_MEMORY,
    IntegraNotifyEvent.ZONES_BYPASS,
    IntegraNotifyEvent.ZONES_NO_VIOLATION_TROUBLE,
    IntegraNotifyEvent.ZONES_LONG_VIOLATION_TROUBLE,
    IntegraNotifyEvent.ZONES_ISOLATE,
    IntegraNotifyEvent.ZONES_MASKED,
    IntegraNotifyEvent.ZONES_MASKED_MEMORY
]

IntegraOutputsNotifyEvents = [
    IntegraNotifyEvent.OUTPUTS_STATE,
]

IntegraDoorsNotifyEvents = [
    IntegraNotifyEvent.DOORS_OPENED,
    IntegraNotifyEvent.DOORS_OPENED_LONG
]

IntegraTroublesNotifyEvents = [
    IntegraNotifyEvent.TROUBLES_PART1,
    IntegraNotifyEvent.TROUBLES_PART2,
    IntegraNotifyEvent.TROUBLES_PART3,
    IntegraNotifyEvent.TROUBLES_PART4,
    IntegraNotifyEvent.TROUBLES_PART5,
    IntegraNotifyEvent.TROUBLES_PART6,
    IntegraNotifyEvent.TROUBLES_PART7,
    IntegraNotifyEvent.TROUBLES_PART8
]

IntegraTroublesMemoryNotifyEvents = [
    IntegraNotifyEvent.TROUBLES_MEMORY_PART1,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART2,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART3,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART4,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART5,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART6,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART7,
    IntegraNotifyEvent.TROUBLES_MEMORY_PART8
]

IntegraOthersNotifyEvents = [
    IntegraNotifyEvent.RTC_AND_STATUS,
]

IntegraDataNotifyEvents = [
    IntegraNotifyEvent.OUTPUT_POWER,
    IntegraNotifyEvent.ZONE_TEMPERATURE,
]

IntegraAllNotifyEvents = [
    *IntegraPartsNotifyEvents,
    *IntegraZonesNotifyEvents,
    *IntegraOutputsNotifyEvents,
    *IntegraDoorsNotifyEvents,
    *IntegraTroublesNotifyEvents,
    *IntegraTroublesMemoryNotifyEvents,
    *IntegraOthersNotifyEvents
]


class IntegraNotifyObject( IntegraEntity ):

    def __init__( self ):
        super().__init__()

    async def _async_state_changed( self, sender: 'IntegraStateBase', previous: IntegraTypeVal ) -> None:
        pass
