import collections
import asyncio
import logging
import os
import sys
import json

from datetime import datetime
from asyncio import AbstractEventLoop
from enum import StrEnum, Flag, IntEnum
from typing import Any, SupportsIndex, TypeVar, Iterator, Callable, Awaitable

from .channel import IntegraChannelStats
from .commands import IntegraCmdData, IntegraCmdOutputPower, IntegraCmdZoneTemp, IntegraCmdRtcData, IntegraRtcStatus
from .const import DEFAULT_CONN_TIMEOUT
from .base import IntegraEntity, IntegraCaps, IntegraType, IntegraTypeVal, IntegraTroubles, IntegraMap, IntegraArmMode, Integra1stCodeAction
from .client import IntegraClientOpts, IntegraClient, IntegraClientStatus
from .elements import (IntegraElement, IntegraElementType, IntegraElementTypes, IntegraElementFactory, IntegraZoneWithPartsElement,
                       IntegraPartWithObjOptsDepsElement, IntegraOutputWithDurationElement, IntegraExpanderElement, IntegraPartOptions, IntegraOutputElementSwitchable, IntegraOutputElementType, IntegraExpanderType, IntegraZoneReactionType,
                       IntegraManipulatorType, IntegraManipulatorElement)
from .notify import IntegraNotifyEvent, IntegraNotifyObject, IntegraNotifySource
from .troubles import IntegraTroublesRegionDef, IntegraTroublesSource, IntegraTroublesZone, IntegraTroublesExp, IntegraTroublesMan, IntegraTroublesSystemMain, IntegraTroublesSystemOther, IntegraTroublesDataType

_LOGGER = logging.getLogger( __name__ )


class Events( StrEnum ):
    EVENT_SYS_CLIENT_EVENT = "event_sys_client_event"
    EVENT_SYS_EVENT = "event_sys_event"
    EVENT_SYS_STATE_CHANGED = "event_sys_state_changed"
    EVENT_SYS_ITEM_CHANGED = "event_sys_item_changed"


AsyncEventHandler = Callable[ [ str, dict[ str, Any ] ], Awaitable[ None ] ]


class EventsDispatcher:

    def __init__( self ) -> None:
        super().__init__()
        self._handlers: dict[ str, list[ AsyncEventHandler ] ] = collections.defaultdict( list )

    def subscribe( self, event_name: str, handler: AsyncEventHandler ):
        self._handlers[ event_name ].append( handler )

    def unsubscribe( self, event_name: str, handler: AsyncEventHandler ) -> None:
        self._handlers[ event_name ].remove( handler )

    async def async_dispatch( self, event_name: str, **kwargs ):
        handlers = self._handlers[ event_name ]
        if handlers:
            await asyncio.gather( *[ handler( event_name, **kwargs ) for handler in handlers ] )


class IntegraStateBase( IntegraEntity ):

    def __init__( self, owner: IntegraNotifyObject, value: IntegraTypeVal ):
        super().__init__()
        self._owner = owner
        self._value: IntegraTypeVal = value

    @property
    def owner( self ):
        return self._owner

    @property
    def value( self ) -> IntegraTypeVal:
        return self._value

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Value": f"{self._value}",
        } )

    async def update( self, current: IntegraTypeVal ):
        previous = self._value
        self._value = current
        if previous != current and self.owner is not None:
            await self.owner._async_state_changed( self, previous )


class IntegraStateEvent( IntegraStateBase ):

    def __init__( self, owner: IntegraNotifyObject, notify_event: IntegraNotifyEvent, value: IntegraTypeVal ):
        super().__init__( owner, value )
        self._notify_event = notify_event

    @property
    def notify_event( self ):
        return self._notify_event

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Event": f"{self._notify_event.name}",
        } )


class IntegraStateFlag( IntegraStateBase ):

    def __init__( self, owner: IntegraNotifyObject, flag: Flag, value: IntegraTypeVal ):
        super().__init__( owner, value )
        self._flag = flag

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Flag": f"{self._flag.name}",
        } )

    async def update( self, current: IntegraTypeVal ):
        await super().update( current & self._flag == self._flag )


DATA = TypeVar( "DATA", bound=IntegraElement )

IntegraSetType = 'IntegraSet'
IntegraSystemType = 'IntegraSystem'


class IntegraItem[ DATA ]( IntegraNotifyObject ):
    item_name: str = ""

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        pass

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__()
        self._owner: IntegraSetType = owner
        self._no: int = no
        self._states: dict[ IntegraNotifyEvent, IntegraStateEvent ] = { }
        self._data: DATA | None = None
        self._dispatcher: EventsDispatcher = EventsDispatcher()

    @property
    def no( self ):
        return self._no

    @property
    def id_str( self ) -> str:
        return f"{self.item_name}_{self.no}"

    @property
    def name( self ) -> str:
        return self._data.name if self._data is not None else f"{self.__class__.__name__}-{self.no}"

    @property
    def client( self ) -> IntegraClient | None:
        return self._owner.client if self._owner is not None else None

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "No": self.no,
            "Name": f"'{self.name}'",
        } )

    def _add_state( self, notify_event: IntegraNotifyEvent, value: IntegraTypeVal ) -> IntegraStateEvent:
        result = IntegraStateEvent( self, notify_event, value )
        self._states.update( { notify_event: result } )
        return result

    async def async_do_state_change( self, notify_event: IntegraNotifyEvent, value: IntegraTypeVal ) -> None:
        if notify_event in self._states:
            await self._states[ notify_event ].update( value )

    def _get_troubles_value( self, values: dict[IntEnum, Flag] ) -> Flag | None:
        pass

    async def _async_do_troubles_change( self, set_value: bool, value: Flag ):
        pass

    async def async_do_troubles_changes( self, set_value: bool, values: dict[IntEnum, Flag] ) -> None:
        value = self._get_troubles_value(values)
        if value is not None:
            await self._async_do_troubles_change( set_value, value )

    async def _async_state_changed( self, sender: IntegraStateBase, previous: IntegraTypeVal ) -> None:
        await super()._async_state_changed( sender, previous )
        if self._owner is not None:
            await self._owner.async_item_changed( self, sender, previous )
        await self._dispatcher.async_dispatch( Events.EVENT_SYS_STATE_CHANGED, sender=self, source=sender, previous=previous )

    async def load_data( self, client: IntegraClient, element_data: DATA | None ) -> DATA | None:
        if element_data is None:
            element_data = await self.item_reader( client, self.no )
        self._data = element_data
        return element_data


ITEM = TypeVar( "ITEM", bound=IntegraItem )


class IntegraSet[ ITEM ]( SupportsIndex ):
    class IntegraSetIterator[ ITEMx ]( Iterator[ ITEMx ] ):

        def __init__( self, items: dict[ int, ITEMx ] ) -> None:
            self._items = items
            self._keys = [ key for key in items.keys() ]
            self._index = 0

        def __next__( self ) -> ITEMx:
            if self._index >= len( self._keys ):
                raise StopIteration
            result = self._items.get( self._keys[ self._index ] )
            self._index += 1
            return result

    set_id: int = -1
    set_name: str = ""
    item_class: type[ ITEM ] = None
    handle_notify_source: IntegraNotifySource | None = None
    handle_troubles_source: IntegraTroublesSource | None = None

    @classmethod
    def register( cls ) -> int:
        cls.set_id = IntegraSetFactory.register( cls )
        return cls.set_id

    def __index__( self ) -> int:
        return len( self._items )

    def __iter__( self ) -> Iterator[ ITEM ]:
        return IntegraSet.IntegraSetIterator[ ITEM ]( self._items )

    def __len__( self ) -> int:
        return len( self._items )

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__()
        self._owner: IntegraSystemType = owner
        self._items: dict[ int, ITEM ] = { }

    def __getitem__( self, item ) -> ITEM | None:
        return self._items.get( item, None )

    @property
    def client( self ) -> IntegraClient | None:
        return self._owner.client if self._owner is not None else None

    def init( self, caps: IntegraCaps ) -> None:
        if self.item_class is None or not hasattr( caps, self.set_name ):
            return

        for item_no in range( 1, getattr( caps, self.set_name ) + 1 ):
            if item_no not in self._items:
                self._items[ item_no ] = self.item_class( self, item_no )
            else:
                _LOGGER.debug( f"Item {self.item_class.__class__.__name__}:{item_no} already initialized",  )

    def get( self, item_no: int ) -> ITEM | None:
        if item_no in self._items:
            return self._items[ item_no ]
        return None

    async def process_state_change( self, notify_event: IntegraNotifyEvent, state_change: dict[ int, IntegraTypeVal ] ) -> None:

        for item_no, state_value in state_change.items():
            item = self.get( item_no )
            if item is not None:
                await item.async_do_state_change( notify_event, state_value )

    async def process_troubles_change( self, region: IntegraTroublesRegionDef, objects: dict[ int, bool ] ):
        for item_no, trouble_change in objects.items():
            item = self.get( item_no )
            if item is not None:
                await  item.async_do_troubles_changes( trouble_change, region.values )

    async def async_item_changed( self, item: IntegraItem, state: IntegraStateBase, previous: IntegraTypeVal ):
        if self._owner is not None:
            await self._owner.async_item_changed( item, state, previous )


class IntegraSetFactory:
    _registry: dict[ int, type ] = { }

    @classmethod
    def register( cls, set_class ) -> int:
        set_id: int = len( cls._registry )
        cls._registry.update( { set_id: set_class } )
        return set_id

    @classmethod
    def get_all( cls ):
        return cls._registry


class IntegraObject( IntegraItem ):
    item_name = "object"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_object_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )

    @property
    def in_use( self ) -> bool:
        return False


class IntegraObjects( IntegraSet[ IntegraObject ] ):
    set_name = "objects"
    item_class = IntegraObject

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraPart( IntegraItem[ IntegraPartWithObjOptsDepsElement ] ):
    item_name = "part"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_part_with_obj_opts_deps_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )
        self._armed_suppresed: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ARMED_SUPPRESSED, False )
        self._armed_really: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ARMED_REALLY, False )
        self._armed_mode1: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ARMED_MODE_1, False )
        self._armed_mode2: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ARMED_MODE_2, False )
        self._armed_mode3: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ARMED_MODE_3, False )
        self._alarm: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ALARM, False )
        self._alarm_memory: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ALARM_MEMORY, False )
        self._fire_alarm: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_FIRE_ALARM, False )
        self._fire_alarm_memory: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_FIRE_ALARM_MEMORY, False )
        self._entry_time: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_ENTRY_TIME, False )
        self._exit_time_a10: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_EXIT_TIME_ABOVE_10, False )
        self._exit_time_b10: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_EXIT_TIME_BELOW_10, False )
        self._first_code_entered: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_1ST_CODE_ENTERED, False )
        self._violated_zones: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_WITH_VIOLATED_ZONES, False )
        self._warning_alarms: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_WITH_WARNING_ALARMS, False )
        self._verified_alarms: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_WITH_VERIFIED_ALARMS, False )
        self._temp_blocked: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_TEMP_BLOCKED, False )
        self._blocked_for_guard: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.PARTS_BLOCKED_FOR_GUARD, False )

    @property
    def dependant_parts( self ) -> list[ int ]:
        return [ ] if self._data is None else self._data.deps

    @property
    def in_use( self ) -> bool:
        return self.object_no > 0

    @property
    def object_no( self ) -> int:
        return -1 if self._data is None else self._data.object_no

    @property
    def options( self ) -> IntegraPartOptions:
        return IntegraPartOptions.NONE if self._data is None else self._data.options

    @property
    def armed_suppressed( self ) -> bool:
        return self._armed_suppresed.value

    @property
    def armed_really( self ) -> bool:
        return self._armed_really.value

    @property
    def armed_mode1( self ) -> bool:
        return self._armed_mode1.value

    @property
    def armed_mode2( self ) -> bool:
        return self._armed_mode2.value

    @property
    def armed_mode3( self ) -> bool:
        return self._armed_mode3.value

    @property
    def alarm( self ) -> bool:
        return self._alarm.value

    @property
    def alarm_memory( self ) -> bool:
        return self._alarm_memory.value

    @property
    def fire_alarm( self ) -> bool:
        return self._fire_alarm.value

    @property
    def fire_alarm_memory( self ) -> bool:
        return self._fire_alarm_memory.value

    @property
    def entry_time( self ) -> bool:
        return self._entry_time.value

    @property
    def exit_time_a10( self ) -> bool:
        return self._exit_time_a10.value

    @property
    def exit_time_b10( self ) -> bool:
        return self._exit_time_b10.value

    @property
    def first_code_entered( self ) -> bool:
        return self._first_code_entered.value

    @property
    def violated_zones( self ) -> bool:
        return self._violated_zones.value

    @property
    def warning_alarms( self ) -> bool:
        return self._warning_alarms.value

    @property
    def verified_alarms( self ) -> bool:
        return self._verified_alarms.value

    @property
    def temp_blocked( self ) -> bool:
        return self._temp_blocked.value

    @property
    def blocked_for_guard( self ) -> bool:
        return self._blocked_for_guard.value

    async def async_arm( self, mode: IntegraArmMode, force: bool = False, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_arm( mode, [ self.no ], force, False, user_code )
        return False

    async def async_disarm( self, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_disarm( [ self.no ], user_code )
        return False

    async def async_clear_alarm( self, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_clear_alarm( [ self.no ], user_code )
        return False

    async def async_enter_1st_code( self, action: Integra1stCodeAction, validity_period: int, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_enter_1st_code( [ self.no ], action, validity_period, user_code )
        return False

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "InUse": f"{self.in_use}",
            "Options": f"{self.options}",
            "Dependents": f"{self.dependant_parts}",
        } )
        pass


class IntegraParts( IntegraSet[ IntegraPart ] ):
    set_name = "parts"
    item_class = IntegraPart
    handle_notify_source = IntegraNotifySource.PARTS

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraZone( IntegraItem[ IntegraZoneWithPartsElement ] ):
    item_name = "zone"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_zone_with_parts_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )
        self._violation: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_VIOLATION, False )
        self._tamper: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_TAMPER, False )
        self._tamper_memory: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_TAMPER, False )
        self._alarm: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_ALARM, False )
        self._alarm_memory: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_ALARM_MEMORY, False )
        self._tamper_alarm_memory: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_TAMPER_ALARM_MEMORY, False )
        self._masking: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_MASKED, False )
        self._masking_memory: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_MASKED_MEMORY, False )
        self._bypass: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_BYPASS, False )
        self._isolate: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_ISOLATE, False )
        self._no_violation_trouble: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_NO_VIOLATION_TROUBLE, False )
        self._long_violation_trouble: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONES_LONG_VIOLATION_TROUBLE, False )

        self._temperature: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.ZONE_TEMPERATURE, 0.0 )
        self._troubles: IntegraStateBase = IntegraStateBase(self, IntegraTroublesZone.NONE )

    @property
    def violation( self ) -> bool:
        return self._violation.value

    @property
    def tamper( self ) -> bool:
        return self._tamper.value

    @property
    def tamper_memory( self ) -> bool:
        return self._tamper_memory.value

    @property
    def alarm( self ) -> bool:
        return self._alarm.value

    @property
    def alarm_memory( self ) -> bool:
        return self._alarm_memory.value

    @property
    def tamper_alarm_memory( self ) -> bool:
        return self._tamper_alarm_memory.value

    @property
    def masking( self ) -> bool:
        return self._masking.value

    @property
    def masking_memory( self ) -> bool:
        return self._masking_memory.value

    @property
    def bypass( self ) -> bool:
        return self._bypass.value

    @property
    def isolate( self ) -> bool:
        return self._isolate.value

    @property
    def no_violation_trouble( self ) -> bool:
        return self._no_violation_trouble.value

    @property
    def long_violation_trouble( self ) -> bool:
        return self._long_violation_trouble.value

    @property
    def temperature( self ) -> float:
        return self._temperature.value

    @property
    def temp_monitor( self ) -> float:
        client = self.client
        if client:
            return client.temp_monitor_get( self.no )
        return 0.0

    @temp_monitor.setter
    def temp_monitor( self, value : float ):
        client = self.client
        if client:
            client.temp_monitor_set( { self.no: value } )

    @property
    def troubles( self ) -> IntegraTroublesZone:
        if isinstance( self._troubles.value, IntegraTroublesZone ):
            return self._troubles.value
        return IntegraTroublesZone.NONE

    def _get_troubles_value( self, values: dict[IntEnum, Flag] ) -> Flag | None:
        if IntegraZoneReactionType.ANY in values:
            return values[IntegraZoneReactionType.ANY]
        return super()._get_troubles_value(values)

    async def _async_do_troubles_change( self, set_value: bool, value: Flag ) -> None:
        await super()._async_do_troubles_change( set_value, value )
        if set_value:
            await self._troubles.update(self._troubles.value | value )
        else:
            await self._troubles.update( self._troubles.value & ~value )

    async def async_isolate( self, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_zones_isolate( [ self.no ], user_code )
        return False

    async def async_bypass( self, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_zones_bypass_set( [ self.no ], user_code )
        return False

    async def async_unbypass( self, user_code: str = "" ) -> bool:
        client = self.client
        if client:
            return await client.async_ctrl_zones_bypass_unset( [ self.no ], user_code )
        return False


class IntegraZones( IntegraSet[ IntegraZone ] ):
    set_name = "zones"
    item_class = IntegraZone
    handle_notify_source = IntegraNotifySource.ZONES
    handle_troubles_source = IntegraTroublesSource.ZONES

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraOutput( IntegraItem[ IntegraOutputWithDurationElement ] ):
    item_name = "output"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_output_with_duration_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )
        self._state: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.OUTPUTS_STATE, False )
        self._power: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.OUTPUT_POWER, 0.0 )

    @property
    def state( self ) -> bool:
        return self._state.value

    @property
    def power( self ) -> float:
        return self._power.value

    @property
    def power_monitor( self ) -> float:
        client = self.client
        if client:
            return client.power_monitor_get( self.no )
        return 0.0

    @power_monitor.setter
    def power_monitor( self, value : float ):
        client = self.client
        if client:
            client.power_monitor_set( { self.no: value } )

    @property
    def output_type( self ) -> IntegraOutputElementType:
        return self._data.output_type if self._data is not None else IntegraOutputElementType.UNUSED__0

    async def async_toggle( self ) -> bool:
        if self.output_type in IntegraOutputElementSwitchable:
            client = self.client
            if client:
                return await client.async_ctrl_outputs_switch( [ self.no ] )
        return False

    async def async_turn_on( self ) -> bool:
        if self.output_type in IntegraOutputElementSwitchable:
            client = self.client
            if client:
                return await client.async_ctrl_outputs_on( [ self.no ] )
        return False

    async def async_turn_off( self ) -> bool:
        if self.output_type in IntegraOutputElementSwitchable:
            client = self.client
            if client:
                return await client.async_ctrl_outputs_off( [ self.no ] )
        return False


class IntegraOutputs( IntegraSet[ IntegraOutput ] ):
    set_name = "outputs"
    item_class = IntegraOutput
    handle_notify_source = IntegraNotifySource.OUTPUTS

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraExpander( IntegraItem[ IntegraExpanderElement ] ):
    item_name = "expander"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_expander_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )
        self._troubles: IntegraStateBase = IntegraStateBase( self, IntegraTroublesExp.NONE )

    @property
    def expander_type( self ) -> IntegraExpanderType:
        return self._data.expander_type if self._data else IntegraExpanderType.UNKNOWN

    @property
    def troubles( self ) -> IntegraTroublesExp:
        if isinstance(self._troubles.value, IntegraTroublesExp):
            return self._troubles.value
        return IntegraTroublesExp.NONE

    def _get_troubles_value( self, values: dict[IntEnum, Flag] ) -> Flag | None:
        if self._data is not None and self._data.expander_type != IntegraExpanderType.UNKNOWN:
            if self._data.expander_type in values:
                return values[self._data.expander_type]
            if IntegraExpanderType.OTHER in values:
                return values[IntegraExpanderType.OTHER]
        return None

    async def _async_do_troubles_change( self, set_value: bool, value: Flag ) -> None:
        await super()._async_do_troubles_change( set_value, value )

        if set_value:
            await self._troubles.update(self._troubles.value | value )
        else:
            await self._troubles.update( self._troubles.value & ~value )

class IntegraExpanders( IntegraSet[ IntegraExpander ] ):
    set_name = "expanders"
    item_class = IntegraExpander
    handle_troubles_source = IntegraTroublesSource.EXPANDERS

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraDoor( IntegraExpander ):

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )
        self._open: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.DOORS_OPENED, False )
        self._open_long: IntegraStateEvent = super()._add_state( IntegraNotifyEvent.DOORS_OPENED_LONG, False )

    @property
    def open( self ) -> bool:
        return self._open.value

    @property
    def open_long( self ) -> bool:
        return self._open_long.value

    @property
    def is_door( self ) -> bool:
        return self.expander_type in [ IntegraExpanderType.CA_64_DR, IntegraExpanderType.CA_64_SR ]

    async def async_open( self ) -> bool:
        if self.is_door:
            client = self.client
            if client:
                return await client.async_ctrl_door_open( [ self.no ] )
        return False


class IntegraDoors( IntegraExpanders ):
    item_class = IntegraDoor
    handle_notify_source = IntegraNotifySource.DOORS
    handle_troubles_source = None

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraUser( IntegraItem ):
    item_name = "user"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_user_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )


class IntegraUsers( IntegraSet[ IntegraUser ] ):
    set_name = "users"
    item_class = IntegraUser

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraAdmin( IntegraItem ):
    item_name = "admin"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_admin_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )


class IntegraAdmins( IntegraSet[ IntegraAdmin ] ):
    set_name = "admins"
    item_class = IntegraAdmin

    def __init__( self, get_max ) -> None:
        super().__init__( get_max )


class IntegraTimer( IntegraItem ):
    item_name = "timer"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_timer_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )


class IntegraTimers( IntegraSet[ IntegraTimer ] ):
    set_name = "timers"
    item_class = IntegraTimer

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraManipulator( IntegraItem[ IntegraManipulatorElement ] ):
    item_name = "manipulator"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_manipulator_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )
        self._troubles: IntegraStateBase = IntegraStateBase(self, IntegraTroublesMan.NONE )

    def _get_troubles_value( self, values: dict[IntEnum, Flag] ) -> Flag | None:
        if self._data is not None and self._data.manipulator_type != IntegraManipulatorType.UNKNOWN:
            if self._data.manipulator_type in values:
                return values[self._data.manipulator_type]
            if IntegraExpanderType.OTHER in values:
                return values[IntegraManipulatorType.OTHER]
        return None

    async def _async_do_troubles_change( self, set_value: bool, value: Flag ) -> None:
        await super()._async_do_troubles_change( set_value, value )

        if set_value:
            await self._troubles.update(self._troubles.value | value )
        else:
            await self._troubles.update( self._troubles.value & ~value )

class IntegraManipulators( IntegraSet[ IntegraManipulator ] ):
    set_name = "manipulators"
    item_class = IntegraManipulator
    handle_troubles_source = IntegraTroublesSource.MANIPULATORS

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraPhone( IntegraItem ):
    item_name = "phone"

    @classmethod
    async def item_reader( cls, client: IntegraClient, element_no: int ):
        return await client.async_read_phone_data( element_no )

    def __init__( self, owner: IntegraSetType, no: int ) -> None:
        super().__init__( owner, no )


class IntegraPhones( IntegraSet[ IntegraPhone ] ):
    set_name = "phones"
    item_class = IntegraPhone

    def __init__( self, owner: IntegraSystemType ) -> None:
        super().__init__( owner )


class IntegraSystem( IntegraNotifyObject ):
    class TaskData:

        def __init__( self, eventloop, task_entry, total: int ) -> None:
            self.current: int = 0
            self._total: int = total
            self._cancelled: bool = False
            self._signal = asyncio.Future()
            self._task = self._system_info_task = eventloop.create_task( task_entry( self ) )

        def cancel( self ):
            self._cancelled = True

        def finished( self, result: bool ):
            self._signal.set_result( result )

        async def wait( self, timeout: float ) -> bool | None:
            try:
                value = await asyncio.wait_for( self._signal, timeout )
                return value
            except asyncio.TimeoutError:
                self._signal = asyncio.Future()
                return None

        @property
        def cancelled( self ) -> bool:
            return self._cancelled

        @property
        def total( self ) -> int:
            return self._total

    class TaskDataInfoLoad( TaskData ):
        def __init__( self, cache_file: str | None, reload: list[ str ] | None, *args ):
            super().__init__( *args )
            self._cache_file: str | None = cache_file
            self._reload: list[ str ] | None = reload

        @property
        def cache_file( self ) -> str:
            return self._cache_file

        @property
        def reload( self ) -> list[ str ] | None:
            return self._reload

    @classmethod
    def serial( cls, serial: str, speed: int, eventloop: AbstractEventLoop, opts: IntegraClientOpts ) -> 'IntegraSystem':
        system = cls( eventloop )
        system._set_client( IntegraClient.serial( serial, speed, eventloop, opts ) )
        return system

    @classmethod
    def tcp( cls, host: str, port: int, eventloop: AbstractEventLoop, opts: IntegraClientOpts ) -> 'IntegraSystem':
        system = cls( eventloop )
        system._set_client( IntegraClient.tcp( host, port, eventloop, opts ) )
        return system

    def __init__( self, eventloop: AbstractEventLoop ) -> None:
        super().__init__()
        self._eventloop: AbstractEventLoop = eventloop
        self._client: IntegraClient | None = None
        self._client_event: EventsDispatcher = EventsDispatcher()

        self._sets: dict = {  }
        for set_id, set_class in IntegraSetFactory.get_all().items():
            self._sets[ set_id ] = set_class( self )

        self._system_info_load: IntegraSystem.TaskData | None = None
        self._dispatcher: EventsDispatcher = EventsDispatcher()
        self._flags: dict[type[Flag], list[IntegraStateFlag]] = { }
        self._service_mode: IntegraStateFlag = self._add_flag( IntegraRtcStatus.SERVICE_MODE, False )
        self._system_troubles: IntegraStateFlag = self._add_flag( IntegraRtcStatus.TROUBLES, False )
        self._system_troubles_memory: IntegraStateFlag = self._add_flag( IntegraRtcStatus.TROUBLES_MEMORY, False )
        self._acu_100_present: IntegraStateFlag = self._add_flag( IntegraRtcStatus.ACU_100_PRESENT, False )
        self._int_rx_present: IntegraStateFlag = self._add_flag( IntegraRtcStatus.INT_RX_PRESENT, False )
        self._grade23_set: IntegraStateFlag = self._add_flag( IntegraRtcStatus.GRADE23_SET, False )

        self._troubles_main: IntegraStateBase = IntegraStateBase( self, IntegraTroublesSystemMain.NONE )
        self._troubles_other: IntegraStateBase = IntegraStateBase( self, IntegraTroublesSystemOther.NONE )
        self._troubles_memory_main: IntegraStateBase = IntegraStateBase( self, IntegraTroublesSystemMain.NONE )
        self._troubles_memory_other: IntegraStateBase = IntegraStateBase( self, IntegraTroublesSystemOther.NONE )
        
    @property
    def caps( self ) -> IntegraCaps:
        return self._client.caps if self._client is not None else IntegraMap.type_to_caps( IntegraType.INTEGRA_UNKNOWN )

    @property
    def client( self ) -> IntegraClient:
        return self._client

    @property
    def status( self ) -> IntegraClientStatus:
        return IntegraClientStatus.DISCONNECTED if self._client is None else self._client.status

    @property
    def objects( self ) -> IntegraObjects:
        return self._sets[ IntegraObjects.set_id ]

    @property
    def parts( self ) -> IntegraParts:
        return self._sets[ IntegraParts.set_id ]

    @property
    def zones( self ) -> IntegraZones:
        return self._sets[ IntegraZones.set_id ]

    @property
    def outputs( self ) -> IntegraOutputs:
        return self._sets[ IntegraOutputs.set_id ]

    @property
    def doors( self ) -> IntegraDoors:
        return self._sets[ IntegraDoors.set_id ]

    @property
    def expanders( self ) -> IntegraExpanders:
        return self._sets[ IntegraExpanders.set_id ]

    @property
    def manipulators( self ) -> IntegraManipulators:
        return self._sets[ IntegraManipulators.set_id ]

    def subscribe( self, event_name: str, event_handler: AsyncEventHandler ) -> None:
        self._dispatcher.subscribe( event_name, event_handler )

    async def _async_system_info_load( self, elements_cache: dict[ str, Any ] | None, instance: IntegraSet, task_data: TaskDataInfoLoad ) -> bool:

        result = False
        reload = True if task_data.reload is not None and (len( task_data.reload ) == 0 or instance.set_name in task_data.reload) else False
        for item in instance:
            element_data: IntegraElement | None = None
            item_id_str = item.id_str
            if not reload and item_id_str in elements_cache:
                element_json = elements_cache[ item_id_str ]
                if "element_type" in element_json and element_json[ "element_type" ] in IntegraElementTypes:
                    element_type = IntegraElementType( element_json[ "element_type" ] )
                    if IntegraElementFactory.exists( instance.set_name, element_type ):
                        element_class = IntegraElementFactory.get_class( instance.set_name, element_type )
                        element_data = element_class.from_json( element_json )

            loaded_element_data = await item.load_data( self._client, element_data )
            if loaded_element_data != element_data:
                elements_cache.update( { item_id_str: loaded_element_data.to_json() } )
                result = True

            task_data.current += 1

        return result

    async def _system_info_load_task( self, task_data: TaskDataInfoLoad ) -> None:
        asyncio.current_task().set_name( f"_system_info_load_task" )
        result = False
        try:
            cache = { "integra_type": self._client.integra_version.integra_type, "elements": { } }
            write_on_exit = True

            if task_data.cache_file is not None and os.path.exists( task_data.cache_file ):
                # noinspection PyBroadException
                try:
                    cache = json.loads( open( task_data.cache_file ).read() )
                    write_on_exit = False
                except:  # pylint: disable=broad-except
                    pass

            for _, instance in self._sets.items():
                if instance.set_name not in cache[ "elements" ]:
                    cache[ "elements" ].update( { instance.set_name: { } } )
                    write_on_exit = True
                elements_cache = cache[ "elements" ][ instance.set_name ]

                if await self._async_system_info_load( elements_cache, instance, task_data ):
                    write_on_exit = True

            if write_on_exit and task_data.cache_file is not None:
                with open( task_data.cache_file, 'w' ) as f:
                    json.dump( cache, f, indent=2 )
                    f.flush()

            result = not task_data.cancelled
        except Exception as e:
            task_data.cancel()
            result = e

        finally:
            # _LOGGER.debug( f"LOAD_TASK: Done. Signaling feature ({result})" )
            task_data.finished( result )

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )

    def _add_flag( self, flag: Flag, value: IntegraTypeVal ) -> IntegraStateFlag:
        result = IntegraStateFlag( self, flag, value )
        self._flags.setdefault( flag.__class__, [] ).append( result )
        return result

    def _init_system( self ) -> None:
        for _, set_instance in self._sets.items():
            set_instance.init( self.caps )

    async def _async_state_changed( self, sender: IntegraStateBase, previous: IntegraTypeVal ) -> None:
        await super()._async_state_changed( sender, previous )
        await self._dispatcher.async_dispatch( Events.EVENT_SYS_EVENT, sender=self, state=sender, previous=previous )

    def _set_client( self, client: IntegraClient ) -> None:
        if self._client is not None:
            self._client.on_event = None
            self._client.on_state_changed = None
            self._client.on_data_changed = None
            self._client.on_troubles_changed = None

        self._client = client

        if self._client is not None:
            self._client.on_event = self._async_client_event_handler
            self._client.on_state_changed = self._async_client_state_changed_handler
            self._client.on_data_changed = self._async_client_data_changed_handler
            self._client.on_troubles_changed = self._async_client_troubles_changed_handler

    async def _async_client_event_handler( self, client: IntegraClient, event: IntegraClientStatus ) -> None:
        await self._dispatcher.async_dispatch( Events.EVENT_SYS_CLIENT_EVENT, sender=self, event=event )
        if event == IntegraClientStatus.CONNECTED:
            self._init_system()

    async def _async_client_state_changed_handler( self, client: IntegraClient, source: IntegraNotifySource, notify_event: IntegraNotifyEvent, state: dict[ int, bool ] ) -> None:
        for _, instance in self._sets.items():
            if instance.handle_notify_source == source:
                await instance.process_state_change( notify_event, state )

    async def _async_client_data_changed_handler( self, client: IntegraClient, source: IntegraNotifySource, notify_event: IntegraNotifyEvent, data: IntegraCmdData ) -> None:

        if notify_event == IntegraNotifyEvent.OUTPUT_POWER and isinstance( data, IntegraCmdOutputPower ):
            await self.outputs.get( data.output_no ).async_do_state_change( notify_event, data.power )
        elif notify_event == IntegraNotifyEvent.ZONE_TEMPERATURE and isinstance( data, IntegraCmdZoneTemp ):
            await self.zones.get( data.zone_no ).async_do_state_change( notify_event, data.temp )
        elif notify_event == IntegraNotifyEvent.RTC_AND_STATUS and isinstance( data, IntegraCmdRtcData ):
            await self._async_do_flag_change( data.status )
        return

    async def _async_client_troubles_changed_handler( self, client: IntegraClient, region: IntegraTroublesRegionDef, objects: IntegraTroublesDataType ) -> None:
        if region.source == IntegraTroublesSource.SYSTEM_MAIN:
            await self._troubles_main.update(objects)
        elif region.source == IntegraTroublesSource.SYSTEM_OTHER:
            await self._troubles_other.update(objects)
        else:
            for _, instance in self._sets.items():
                if instance.handle_troubles_source == region.source:
                    await instance.process_troubles_change( region, objects )

    async def _async_do_flag_change( self, flag : Flag ) -> None:
        if flag.__class__ in self._flags:
            for state_flag in self._flags[flag.__class__]:
                await state_flag.update( flag )

    async def async_item_changed( self, item: IntegraItem, state: IntegraStateBase, previous: IntegraTypeVal ) -> None:
        await self._dispatcher.async_dispatch( Events.EVENT_SYS_ITEM_CHANGED, sender=self, item=item, state=state, previous=previous )

    def get_channel_stats( self ) -> IntegraChannelStats | None:
        if self._client is not None:
            return self._client.stats
        return None

    def system_info_load( self, cache_file: str = None, reload: list[ str ] | None = None ) -> bool:
        if self._system_info_load is None:
            total = 0
            for _, instance in self._sets.items():
                total += len( instance )
            self._system_info_load = IntegraSystem.TaskDataInfoLoad( cache_file, reload, self._eventloop, self._system_info_load_task, total )
            return True

        return False

    async def async_system_info_wait_for( self, progress: Callable[ [ int, int ], Awaitable[ bool ] ] | None = None, timeout: float = -1 ) -> bool | None:

        result: bool | None = None
        if self._system_info_load is not None:

            in_time = datetime.now()
            last = 0
            try:
                while True:
                    if progress is not None and not self._system_info_load.cancelled:
                        if last != self._system_info_load.current:
                            last = self._system_info_load.current
                            if not await progress( self._system_info_load.current, self._system_info_load.total ):
                                self._system_info_load.cancel()

                    value = await self._system_info_load.wait( 2.0 )
                    if value is None:
                        out_time = datetime.now()
                        if 0 < timeout < (out_time - in_time).total_seconds():
                            result = False
                            break
                    elif isinstance( value, Exception ):
                        _LOGGER.exception( f"LOAD_TASK: Exception while reading object info: {value}" )
                        break
                    else:
                        result = value
                        break
            finally:
                if progress is not None and not self._system_info_load.cancelled:
                    if last != self._system_info_load.current:
                        await progress( self._system_info_load.current, self._system_info_load.total )

        return result

    async def async_connect( self, retries: int = 0, timeout: float | None = None ) -> bool:
        if self._client is not None:
            return await self._client.async_connect( retries=retries, timeout=timeout )
        return False

    async def async_read_troubles( self, memory: bool ) -> bytes | None:
        result = bytes()
        if self._client is not None:
            for trouble in IntegraTroubles:
                memory_block = await self._client.async_read_troubles( trouble, memory )
                if result is not None:
                    result += memory_block
                else:
                    return None
        return result

    def monitor_configure( self ):
        return self.client.system_monitor_configure()

    async def async_monitor_start( self, notify_events: list[ IntegraNotifyEvent ] ) -> bool:
        if self._client is not None:
            await self._client.async_notify_events_setup( notify_events )
            return True
        return False

    async def async_monitor_stop( self ) -> bool:
        if self._client is not None:
            await self._client.async_notify_events_setup( None )
            return True
        return False

    async def async_disconnect( self ) -> None:
        if self._client is not None:
            await self._client.async_disconnect()

    async def async_power_temp_update( self ) -> None:
        if self._client is not None:
            await self._client.async_read_output_power( 23 )
            await self._client.async_read_zone_temperature( 21 )

    async def async_troubles_clear_mem( self, user_code: str = "" ) -> bool:
        if self._client is not None:
            return await self._client.async_ctrl_trouble_mem_clear( user_code )
        return False

    async def async_set_rtc_clock( self, date: datetime | None = None, user_code: str = "" ) -> bool:
        if self._client is not None:
            return await self._client.async_ctrl_set_rtc_clock( self, date, user_code )
        return False


def __register_sets( source ):
    for module_item in source:
        if not module_item.startswith( "Integra" ):
            continue
        type_ = getattr( sys.modules[ __name__ ], module_item )
        try:
            if issubclass( type_, IntegraSet ) and type_ != IntegraSet:
                type_.register()
        except TypeError:
            continue


__register_sets( dir() )
