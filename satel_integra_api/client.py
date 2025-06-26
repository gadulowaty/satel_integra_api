import asyncio
import json
import os
import datetime
import logging
import traceback

from enum import IntEnum

_LOGGER = logging.getLogger( __name__ )

from datetime import datetime, timedelta

from asyncio import AbstractEventLoop, Task
from typing import Any, Callable, Awaitable

from .const import DEFAULT_CONN_TIMEOUT, DEFAULT_RESP_TIMEOUT, DEFAULT_KEEP_ALIVE
from .base import (IntegraEntity, IntegraType, IntegraBaseType, IntegraCaps, IntegraTroubles,
                   IntegraMap, IntegraArmMode, IntegraModuleCaps, Integra1stCodeAction, IntegraDispatcher, IntegraContextRefCnt, IntegraError, IntegraTaskContextRefCnt)
from .channel import IntegraChannelStats, IntegraChannel, IntegraChannelEvent
from .channel_serial import IntegraChannelRS232
from .channel_tcp import IntegraChannelTCP
from .commands import (IntegraCommand, IntegraCmdData, IntegraCmdEventRecData, IntegraCmdEventTextData,
                       IntegraCmdUserCodeData, IntegraCmdUserParts1stCodeData, IntegraCmdUserPartsData, IntegraCmdUserPartsArmData,
                       IntegraCmdUserZonesData, IntegraCmdUserOutputsData, IntegraCmdUserOutputsExpandersData, IntegraCmdOutputData, IntegraCmdZoneData,
                       IntegraCmdOutputPower, IntegraCmdZoneTemp, IntegraCmdUserSetRtcData, IntegraCmdReadElementData, IntegraCommandHelper, IntegraCmdRawData,
                       IntegraCmdRtcData, IntegraCmdUserCodeNoData, IntegraCmdVersionData, IntegraCmdModuleVersionData, IntegraCmdDoorsData,
                       IntegraCmdPartsData, IntegraCmdZonesData, IntegraCmdOutputsData, IntegraCmdUserSetUserLocksData, IntegraCmdUserCodeNewCodePhoneData,
                       IntegraCmdUserCodeNewCodeUserData, IntegraCmdUserCodeUserData, IntegraCmdUserDevMgmtData,
                       IntegraUserDevMgmtList, IntegraCmdUserDevMgmtUserData, IntegraCmdUserDevMgmtDeviceData)
from .elements import (IntegraElement, IntegraObjectElement, IntegraPartElement, IntegraPartWithObjElement,
                       IntegraPartWithObjOptsElement, IntegraPartWithObjOptsDepsElement, IntegraZoneElement, IntegraZoneWithPartsElement,
                       IntegraOutputElement, IntegraOutputWithDurationElement, IntegraUserElement, IntegraAdminElement,
                       IntegraExpanderElement, IntegraManipulatorElement, IntegraTimerElement, IntegraPhoneElement)
from .events import IntegraEventSource, IntegraEventRecData, IntegraEventTextData, INTEGRA_EVENT_STD_LAST, INTEGRA_EVENT_GRADE_LAST, IntegraEventRecStdData, IntegraEventRecGradeData
from .messages import IntegraResponse, IntegraResponseErrorCode, IntegraResponseErrorCodes, IntegraRequestError
from .notify import (IntegraNotifyEvent, IntegraPartsNotifyEvents, IntegraZonesNotifyEvents, IntegraOutputsNotifyEvents,
                     IntegraOthersNotifyEvents, IntegraDoorsNotifyEvents, IntegraTroublesNotifyEvents, IntegraDataNotifyEvents,
                     IntegraTroublesMemoryNotifyEvents, IntegraNotifySource)
from .users import (IntegraUserSelf, IntegraUserOther, IntegraUser, IntegraUserDeviceMgmtFunc, IntegraUserProximityCard, IntegraUserDallasDev, IntegraUserDeviceMgmtFuncs, IntegraUserIntRxKeyFob,
                    IntegraUserAbaxKeyFob, IntegraUsersList, IntegraUserLocks)
from .troubles import (IntegraTroublesRegionDef, IntegraTroublesSource, IntegraTroublesRegionId, IntegraTroublesRegionDefs, IntegraTroublesSystemMain,
                       IntegraTroublesSystemOther, IntegraTroublesDataType)


class IntegraClientStatus( IntEnum ):
    CONNECTING = 0
    RECONNECTING = 1
    CONNECTED = 2
    DISCONNECTING = 3
    DISCONNECTED = 4


IntegraClientType = 'IntegraClient'

IntegraClientEventCallback = Callable[ [ IntegraClientType, IntegraClientStatus ], Awaitable[ None ] ] | None
IntegraClientStateChangedCallback = Callable[ [ IntegraClientType, IntegraNotifySource, IntegraNotifyEvent, dict[ int, bool ] ], Awaitable[ None ] ] | None
IntegraClientDataChangedCallback = Callable[ [ IntegraClientType, IntegraNotifySource, IntegraNotifyEvent, IntegraCmdData ], Awaitable[ None ] ] | None
IntegraClientTroublesChangedCallback = Callable[ [ IntegraClientType, IntegraTroublesRegionDef, IntegraTroublesDataType ], Awaitable[ None ] ] | None


class IntegraClientError( IntegraError ):

    def __init__( self, message: str ):
        super().__init__()
        self._message = message

    @property
    def message( self ):
        return self._message


class IntegraClientOpts( IntegraEntity ):

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "ConnTimeout": f"{self.conn_timeout:.2f}",
            "RespTimeout": f"{self.resp_timeout:.2f}",
            "KeepAlive": f"{self.keep_alive:.2f}",
            "UserCode": f"{self.user_code}",
            "PrefixCode": f"{self.prefix_code}",
            "IntegrationKey": f"{self.integration_key}",
            "Reconnect": f"{self.reconnect}",
        } )

    def __init__( self ):
        super().__init__()
        self._ro_prefix_code: str = ""
        self._ro_user_code: str = ""
        self._ro_conn_timeout: float = DEFAULT_CONN_TIMEOUT
        self._ro_resp_timeout: float = DEFAULT_RESP_TIMEOUT
        self._ro_keep_alive: float = DEFAULT_KEEP_ALIVE
        self._ro_integration_key: str = ""
        self._ro_reconnect: int = -1

    def get_user_code( self, user_code: str = "" ):
        if user_code.strip( " " ) == "":
            return self.user_code.strip( " " )
        return user_code.strip( "  " )

    @property
    def prefix_code( self ) -> str:
        return self._ro_prefix_code

    @property
    def user_code( self ) -> str:
        return self._ro_user_code

    @property
    def conn_timeout( self ) -> float:
        return self._ro_conn_timeout

    @property
    def resp_timeout( self ) -> float:
        return self._ro_resp_timeout

    @property
    def keep_alive( self ) -> float:
        return self._ro_keep_alive

    @property
    def integration_key( self ) -> str:
        return self._ro_integration_key

    @property
    def reconnect( self ) -> int:
        return self._ro_reconnect

    @classmethod
    def create( cls, **kwargs ) -> 'IntegraClientOpts':
        result = IntegraClientOpts()
        for key, value in kwargs.items():
            attr_name = f"_ro_{key}"
            if hasattr( result, attr_name ):
                setattr( result, "_ro_" + key, value )
            else:
                _LOGGER.error( f"{cls.__name__} does not have attribute '{key}'" )
        return result


class IntegraClient( IntegraEntity ):

    @classmethod
    def serial( cls, serial: str, speed: int, eventloop: AbstractEventLoop, opts: IntegraClientOpts ) -> IntegraClientType:
        client = cls( eventloop, opts )
        channel = IntegraChannelRS232( eventloop, serial, speed, client._async_channel_event_handler )
        client._set_channel( channel )
        return client

    @classmethod
    def tcp( cls, host: str, port: int, eventloop: AbstractEventLoop, opts: IntegraClientOpts ) -> IntegraClientType:
        client = cls( eventloop, opts )
        channel = IntegraChannelTCP( eventloop, host, port, opts.integration_key, client._async_channel_event_handler )
        client._set_channel( channel )
        return client

    def __init__( self, eventloop: AbstractEventLoop, opts: IntegraClientOpts ):
        super().__init__()
        self._eventloop: AbstractEventLoop = eventloop
        self._opts: IntegraClientOpts = opts
        self._channel: IntegraChannel | None = None
        self._status: IntegraClientStatus = IntegraClientStatus.DISCONNECTED
        self._cmd_timeout: float = 5.0
        self._integra_version: IntegraCmdVersionData | None = None
        self._module_version: IntegraCmdModuleVersionData | None = None
        self._caps: IntegraCaps = IntegraMap.type_to_caps( IntegraType.INTEGRA_UNKNOWN )
        self._notify_event_states: dict[ IntegraNotifyEvent, bytes ] = { }
        self._event_dispatcher: IntegraDispatcher | None = None
        self._system_monitor_task: Task | None = None
        self._system_monitor_cfg: IntegraContextRefCnt = IntegraContextRefCnt( self._system_monitor_reconfigure )
        self._request_no_error: IntegraTaskContextRefCnt = IntegraTaskContextRefCnt()
        self._system_monitor_event: asyncio.Event = asyncio.Event()
        self._on_event: IntegraClientEventCallback = None
        self._on_state_changed: IntegraClientStateChangedCallback = None
        self._on_data_changed: IntegraClientDataChangedCallback = None
        self._on_troubles_changed: IntegraClientTroublesChangedCallback = None
        self._cache_troubles: dict[ IntegraTroublesRegionId, bytes ] = { }
        self._poll_interval: float = 0.00
        self._power_monitor: dict[ int, float ] = { }
        self._temp_monitor: dict[ int, float ] = { }
        self._connect_task: Task | None = None
        self._changed_events: list[ IntegraNotifyEvent ] = [ ]
        self._rcvd_events: list[ IntegraNotifyEvent ] = [ ]

    @property
    def opts( self ) -> IntegraClientOpts | None:
        return self._opts

    @property
    def caps( self ) -> IntegraCaps:
        return self._caps

    @property
    def stats( self ) -> IntegraChannelStats | None:
        return self._channel.stats

    @property
    def status( self ) -> IntegraClientStatus:
        return self._status

    @property
    def integra_version( self ) -> IntegraCmdVersionData | None:
        return self._integra_version

    @property
    def module_version( self ) -> IntegraCmdModuleVersionData | None:
        return self._module_version

    @property
    def eventloop( self ) -> AbstractEventLoop:
        return self._eventloop

    @property
    def support_32bytes( self ) -> bool:
        return (self.module_version is not None and IntegraModuleCaps.MODULE_CAP_32BYTE in self.module_version.caps and
                self.integra_version is not None and self.integra_version.integra_type == IntegraBaseType.INTEGRA_256PLUS)

    @property
    def support_troubles67( self ) -> bool:
        return self.module_version is not None and self.module_version.major >= 2

    @property
    def support_troubles8( self ) -> bool:
        return self.module_version is not None and IntegraModuleCaps.MODULE_CAP_TROUBLE8 in self.module_version.caps

    @property
    def poll_interval( self ) -> float | None:
        return self._poll_interval

    @poll_interval.setter
    def poll_interval( self, value: float ):
        if self._poll_interval != value:
            self._poll_interval = value
            self._system_monitor_reconfigure()

    @property
    def on_event( self ) -> IntegraClientEventCallback:
        return self._on_event

    @on_event.setter
    def on_event( self, event ) -> None:
        self._on_event = event

    @property
    def on_state_changed( self ) -> IntegraClientStateChangedCallback:
        return self._on_state_changed

    @on_state_changed.setter
    def on_state_changed( self, state ) -> None:
        self._on_state_changed = state

    @property
    def on_troubles_changed( self ) -> IntegraClientTroublesChangedCallback:
        return self._on_troubles_changed

    @on_troubles_changed.setter
    def on_troubles_changed( self, callback: IntegraClientTroublesChangedCallback ) -> None:
        self._on_troubles_changed = callback

    @property
    def on_data_changed( self ) -> IntegraClientDataChangedCallback:
        return self._on_data_changed

    @on_data_changed.setter
    def on_data_changed( self, callback: IntegraClientDataChangedCallback ) -> None:
        self._on_data_changed = callback

    def _get_diff_state( self, notify_event: IntegraNotifyEvent, current_state: bytes, max_length: int ) -> dict[ int, bool ]:

        max_length = min( int( max_length / 8 ), len( current_state ) )
        current_state = current_state[ : max_length ]

        if not notify_event in self._notify_event_states:
            prev_state = bytes( [ (~byte) & 0xFF for byte in current_state ] )
        else:
            prev_state = self._notify_event_states[ notify_event ]
        self._notify_event_states.update( { notify_event: current_state } )

        result = { }
        for byte_index in range( max_length ):
            byte_diff = prev_state[ byte_index ] ^ current_state[ byte_index ]
            if byte_diff != 0:
                for bit_index in range( 8 ):
                    if (byte_diff & (1 << bit_index)) != 0:
                        result.update( { (byte_index * 8) + (bit_index + 1): True if current_state[ byte_index ] & (1 << bit_index) else False } )
        return result

    def _get_troubles_changed( self, region_id: IntegraTroublesRegionId, current: bytes ) -> dict[ int, bool ]:

        if region_id in self._cache_troubles:
            previous = self._cache_troubles[ region_id ]
        else:
            previous = bytes( [ (~byte) & 0xFF for byte in current ] )
        self._cache_troubles[ region_id ] = current

        result = { }
        for byte_index in range( len( current ) ):
            byte_diff = current[ byte_index ] ^ previous[ byte_index ]
            if byte_diff != 0:
                for bit_index in range( 8 ):
                    if (byte_diff & (1 << bit_index)) != 0:
                        result.update( { (byte_index * 8) + (bit_index + 1): True if current[ byte_index ] & (1 << bit_index) else False } )
        return result

    def _set_channel( self, channel: IntegraChannel ):
        self._channel = channel

    def _check_response( self, response: IntegraResponse | None ) -> bool:
        if response is None:
            if not self._request_no_error.ref_count:
                raise IntegraRequestError( None, IntegraResponseErrorCode.UNKNOWN_ERROR, -1 )
            return False
        if not response.success:
            if not self._request_no_error.ref_count:
                raise IntegraRequestError( response.request.command if response.request else response.command, response.error_code, response.error_code_no )
            else:
                _LOGGER.log( self._request_no_error.log_level, f"{response.request} failed, error code is {response.error_code.name} ({response.error_code_no})" )
            return False
        return True

    @staticmethod
    def _check_response_user( data: bytes ) -> bool:
        if data[ 0 ] == IntegraUserDeviceMgmtFunc.RESULT.value:
            func = IntegraUserDeviceMgmtFunc( data[ 1 ] ) if data[ 1 ] in IntegraUserDeviceMgmtFuncs else IntegraUserDeviceMgmtFunc.UNKNOWN
            func_str = f"{func.name}" if func != IntegraUserDeviceMgmtFunc.UNKNOWN else f"{IntegraUserDeviceMgmtFunc.UNKNOWN.name} (0x{data[ 1 ]:02X}"
            error = IntegraResponseErrorCode( data[ 3 ] ) if data[ 3 ] in IntegraResponseErrorCodes else IntegraResponseErrorCode.UNKNOWN_ERROR
            error_str = f"{error.name}" if error != IntegraResponseErrorCode.UNKNOWN_ERROR else f"{IntegraResponseErrorCode.UNKNOWN_ERROR.name} (0x{data[ 3 ]:02X}"
            if error not in [ IntegraResponseErrorCode.NO_ERROR, IntegraResponseErrorCode.COMMAND_ACCEPTED ]:
                _LOGGER.error( f"User function {IntegraCommand.USER_MANAGE_DEVS.name}:{func_str} for user {data[ 2 ]} failed with error {error_str}" )
                return False
        return True

    def _get_cmd_list_len( self ) -> int:
        if self.support_troubles67:
            return (7 if self.support_troubles8 else 6) * 8
        return 5 * 8

    def _request_data_for_zones( self ) -> bytes | None:
        if self.support_32bytes:
            return bytes( [ 0xFF ] )
        return None

    def _request_data_for_outputs( self ) -> bytes | None:
        if self.support_32bytes:
            return bytes( [ 0xFF ] )
        return None

    async def _system_monitor_proc( self ):

        task_self = asyncio.current_task()
        task_name = task_self.get_name()
        _LOGGER.debug( f"[{task_name}] Starting system monitor" )

        reconfigure: bool = True
        poll_interval: float = 0.0
        poll_last: datetime = datetime.min

        power_mon: dict[ int, float ] = { }
        power_last: dict[ int, datetime ] = { }

        temp_mon: dict[ int, float ] = { }
        temp_last: dict[ int, datetime ] = { }

        if len( self._changed_events ) > 0 or len( self._rcvd_events ) > 0:
            await self._async_system_changes_monitor( IntegraNotifyEvent.to_commands( self._changed_events ), IntegraNotifyEvent.to_commands( self._rcvd_events ) )

        while task_self.cancelling() == 0:
            try:
                if reconfigure:
                    reconfigure = False

                    for output, interval in self._power_monitor.items():
                        if output in power_mon:
                            if power_mon[ output ] != interval:
                                power_mon[ output ] = interval
                                power_last[ output ] = datetime.min
                        else:
                            power_mon.setdefault( output, interval )
                            power_last.setdefault( output, datetime.min )
                    for output in list( power_mon.keys() ):
                        if output not in self._power_monitor:
                            power_mon.pop( output )
                            power_last.pop( output )

                    for zone, interval in self._temp_monitor.items():
                        if zone in temp_mon:
                            if temp_mon[ zone ] != interval:
                                temp_mon[ zone ] = interval
                                temp_last[ zone ] = datetime.min
                        else:
                            temp_mon.setdefault( zone, interval )
                            temp_last.setdefault( zone, datetime.min )
                    for zone in list( temp_mon.keys() ):
                        if zone not in self._temp_monitor:
                            temp_mon.pop( zone )
                            temp_last.pop( zone )

                    if poll_interval != self.poll_interval:
                        poll_interval = self.poll_interval
                        poll_last: datetime = datetime.min

                    _LOGGER.debug( f"[{task_name}] RECONFIGURE: PollInterval={poll_interval}; TempMon={temp_mon}; PowerMon={power_mon}" )

                sleep = 3600.0
                if poll_interval > 0:
                    if (datetime.now() - poll_last).total_seconds() > poll_interval:
                        # _LOGGER.debug( f"[{task_name}] Polling changed events (last {(datetime.now() - poll_last).total_seconds()} ago)" )
                        poll_last = datetime.now()
                        read_cmds = await self.async_read_system_changes()
                        for cmd in read_cmds:
                            notify_event = IntegraNotifyEvent.from_command( cmd )
                            if notify_event in IntegraZonesNotifyEvents:
                                await self._async_send_command( cmd, self._request_data_for_zones() )
                            elif notify_event in IntegraOutputsNotifyEvents:
                                await self._async_send_command( cmd, self._request_data_for_outputs() )
                            else:
                                await self._async_send_command( cmd )
                    poll_next = poll_last + timedelta( seconds=poll_interval )
                    sleep = min( max( (poll_next - datetime.now()).total_seconds(), 0.00 ), sleep )

                for zone, interval in temp_mon.items():
                    if interval > 0:
                        if (datetime.now() - temp_last[ zone ]).total_seconds() > interval:
                            # _LOGGER.debug( f"[{task_name}] Polling temperature for zone {zone} (last {(datetime.now() - temp_last[ zone ]).total_seconds()} ago)" )
                            temp_last[ zone ] = datetime.now()
                            await self.async_read_zone_temperature( zone )
                        poll_next = temp_last[ zone ] + timedelta( seconds=interval )
                        sleep = min( max( (poll_next - datetime.now()).total_seconds(), 0.00 ), sleep )

                for output, interval in power_mon.items():
                    if interval > 0:
                        if (datetime.now() - power_last[ output ]).total_seconds() > interval:
                            # _LOGGER.debug( f"[{task_name}] Polling power for output {output} (last {(datetime.now() - power_last[ output ]).total_seconds()} ago)" )
                            power_last[ output ] = datetime.now()
                            await self.async_read_output_power( output )
                        poll_next = power_last[ output ] + timedelta( seconds=interval )
                        sleep = min( max( (poll_next - datetime.now()).total_seconds(), 0.00 ), sleep )

                # _LOGGER.debug( f"[{task_name}] Next event pooling in {sleep} secs" )
                if sleep > 0:
                    if await asyncio.wait_for( self._system_monitor_event.wait(), sleep ):
                        self._system_monitor_event.clear()
                        # _LOGGER.debug( f"[{task_name}] Reconfigure request" )
                        reconfigure = True
                else:
                    _LOGGER.warning( f"[{task_name}] Polling to short. Reconsider using longer intervals" )

            except IntegraRequestError:
                continue

            except asyncio.TimeoutError:
                continue

            except asyncio.CancelledError:
                # _LOGGER.warning( f"[{task_name}]: CANCELLED" )
                break

            except Exception as err:
                if not isinstance( err, IntegraError ):
                    _LOGGER.debug( f"[{task_name}]: ERROR, {err}\n{traceback.format_exc()}" )
                break

        self._system_monitor_task = None
        _LOGGER.debug( f"[{task_name}]: FINISHED {'(Canceled)' if task_self.cancelling() != 0 else ''}" )

    def _system_monitor_start( self ):
        if self._system_monitor_task is None:
            self._system_monitor_task = asyncio.create_task( self._system_monitor_proc(), name="system_monitor" )

    async def _system_monitor_stop( self ):
        if self._system_monitor_task is None:
            return
        system_monitor = self._system_monitor_task
        self._system_monitor_task = None
        system_monitor.cancel()
        try:
            await system_monitor
        except Exception as err:
            _LOGGER.debug( f"awaiting for task system_monitor finished with {err}" )

    def _system_monitor_reconfigure( self ):
        if self._system_monitor_cfg.ref_count == 0:
            self._system_monitor_event.set()
        else:
            self._system_monitor_cfg.changed = True

    def system_monitor_configure( self ) -> object:
        return self._system_monitor_cfg

    def request_no_error( self, log_level: int = -1 ) -> object:
        self._request_no_error.log_level = log_level
        return self._request_no_error

    async def _async_set_status( self, status: IntegraClientStatus ):
        if self._status != status:
            self._status = status
            if self.on_event is not None:
                await self.on_event( self, self._status )

    async def _async_do_state_changed( self, source: IntegraNotifySource, notify_event: IntegraNotifyEvent, objects: dict[ int, bool ] ):
        if self.on_state_changed is not None:
            await self.on_state_changed( self, source, notify_event, objects )

    async def _async_do_data_changed( self, source: IntegraNotifySource, notify_event: IntegraNotifyEvent, response: IntegraResponse ) -> None:
        if self.on_data_changed is not None:
            command_data = IntegraCmdData.from_command( response.command, response.data )
            if command_data is not None:
                await self.on_data_changed( self, source, notify_event, command_data )
        return None

    async def _async_do_troubles_changed( self, channel: IntegraChannel, notify_event: IntegraNotifyEvent, data: bytes ) -> None:
        data = list( data )
        if notify_event == IntegraNotifyEvent.TROUBLES_PART1:
            # data[40] = 0xFF
            # data[46] = 0xFF
            pass
        elif notify_event == IntegraNotifyEvent.TROUBLES_PART2:
            # data[0] = 0xFF
            pass
        elif notify_event == IntegraNotifyEvent.TROUBLES_PART4:
            # data[27] = 0xFF
            pass
        data = bytes( data )

        regions = IntegraTroublesRegionDefs.get_regions( notify_event )
        for region in regions:
            if region.source in [ IntegraTroublesSource.ZONES, IntegraTroublesSource.EXPANDERS, IntegraTroublesSource.MANIPULATORS ]:
                objects = self._get_troubles_changed( region.region_id, region.get_data( data ) )
                if self.on_troubles_changed is not None and len( objects ) > 0:
                    await self.on_troubles_changed( self, region, objects )
            elif region.source == IntegraTroublesSource.SYSTEM_MAIN:
                value = IntegraTroublesSystemMain( int.from_bytes( region.get_data( data ), byteorder="little" ) )
                await self.on_troubles_changed( self, region, value )
            elif region.source == IntegraTroublesSource.SYSTEM_OTHER:
                value = IntegraTroublesSystemOther( int.from_bytes( region.get_data( data ), byteorder="little" ) )
                await self.on_troubles_changed( self, region, value )

    async def _async_do_troubles_mem_changed( self, channel: IntegraChannel, notify_event: IntegraNotifyEvent, data: bytes ) -> None:
        pass

    async def _async_do_channel_connected( self, channel: IntegraChannel ):

        if self._event_dispatcher is not None:
            await self._event_dispatcher.shutdown( self, "_event_dispatcher" )
        self._event_dispatcher = IntegraDispatcher.create( self._async_process_channel_event )

        self._integra_version = await self.async_read_integra_version()
        self._module_version = await self.async_read_module_version()
        self._caps = IntegraMap.type_to_caps( self.integra_version.integra_type )
        self._system_monitor_start()

        await self._async_set_status( IntegraClientStatus.CONNECTED )

    async def _async_do_channel_disconnected( self, channel: IntegraChannel, should_reconnect: bool ):

        await self._system_monitor_stop()

        if self._event_dispatcher is not None:
            await self._event_dispatcher.shutdown( self, "_event_dispatcher" )

        if self._status == IntegraClientStatus.CONNECTED and self.opts.reconnect and should_reconnect:
            await self._async_connect_task_start( self.opts.reconnect, self.opts.conn_timeout, IntegraClientStatus.RECONNECTING )
        elif self._connect_task is None:
            await self._async_set_status( IntegraClientStatus.DISCONNECTED )

    async def _async_do_channel_notification( self, channel: IntegraChannel, response: IntegraResponse ):

        notify_event = IntegraNotifyEvent.from_command( response.command )
        if notify_event is not None:
            if notify_event in IntegraPartsNotifyEvents:
                await self._async_do_state_changed( IntegraNotifySource.PARTS, notify_event, self._get_diff_state( notify_event, response.data, self.caps.parts ) )

            elif notify_event in IntegraZonesNotifyEvents:
                await self._async_do_state_changed( IntegraNotifySource.ZONES, notify_event, self._get_diff_state( notify_event, response.data, self.caps.zones ) )

            elif notify_event in IntegraOutputsNotifyEvents:
                await self._async_do_state_changed( IntegraNotifySource.OUTPUTS, notify_event, self._get_diff_state( notify_event, response.data, self.caps.outputs ) )

            elif notify_event in IntegraDoorsNotifyEvents:
                await self._async_do_state_changed( IntegraNotifySource.DOORS, notify_event, self._get_diff_state( notify_event, response.data, self.caps.doors ) )


            elif notify_event in IntegraDataNotifyEvents or notify_event in IntegraOthersNotifyEvents:
                await self._async_do_data_changed( IntegraNotifySource.DATA, notify_event, response )

            elif notify_event in IntegraTroublesNotifyEvents:
                await self._async_do_troubles_changed( channel, notify_event, response.data )

            elif notify_event in IntegraTroublesMemoryNotifyEvents:
                await self._async_do_troubles_mem_changed( channel, notify_event, response.data )

    async def _async_process_channel_event( self, sender: IntegraChannel, event: IntegraChannelEvent, data: Any ) -> None:

        if event == IntegraChannelEvent.CONNECTED:
            await self._async_do_channel_connected( sender )

        elif event == IntegraChannelEvent.NOTIFICATION:
            await self._async_do_channel_notification( sender, data )

        elif event == IntegraChannelEvent.DISCONNECTED:
            await self._async_do_channel_disconnected( sender, data )

        return

    async def _async_channel_event_handler( self, sender: IntegraChannel, event: IntegraChannelEvent, data: Any = None ) -> None:
        if self._channel.is_channel_ctx( asyncio.current_task() ):
            if self._event_dispatcher is not None:
                await self._event_dispatcher.put( sender=sender, event=event, data=data )
            else:
                _LOGGER.error( "Event queue does not exists, event lost" )
        else:
            await self._async_process_channel_event( sender, event, data )

    async def _async_connect_task( self, retries: int, timeout: float, conn_result: asyncio.Future ):
        task_self = asyncio.current_task()
        task_name = task_self.get_name()
        task_err: BaseException | None = None

        _LOGGER.debug( f"[{task_name}]: STARTING (retries={retries}, timeout={timeout})" )

        try:
            sleep = 5
            sleep_step = 3
            while True:
                self._channel._port = 17094 if (retries < 0 or retries > 0) and self.status == IntegraClientStatus.RECONNECTING else 7094

                try:
                    if await self._channel.async_connect( timeout ):
                        task_err = None
                        break
                except IntegraError as err:
                    task_err = err

                if retries > 0:
                    retries -= 1

                if retries == 0:
                    break

                if retries > 0:
                    _LOGGER.info( f"[{task_name}]: sleeping for {sleep} seconds ({retries} retries)..." )
                else:
                    _LOGGER.info( f"[{task_name}]: sleeping for {sleep} seconds..." )
                await asyncio.sleep( sleep )
                if sleep < 500 and sleep_step > 0:
                    sleep *= sleep_step

        except asyncio.CancelledError:
            # _LOGGER.debug( f"[{task_name}]: CANCELLED" )
            pass

        finally:
            self._connect_task = None
            if not self._channel.connected and self._status in [ IntegraClientStatus.CONNECTING, IntegraClientStatus.RECONNECTING ]:
                await self._async_set_status( IntegraClientStatus.DISCONNECTED )

            if task_self.cancelling() != 0:
                _LOGGER.debug( f"[{task_name}]: FINISHED (Cancelled)" )
                conn_result.set_result( False )
            elif retries == 0 or task_err is not None:
                _LOGGER.debug( f"[{task_name}]: FINISHED ({task_err if task_err is not None else 'Retries Exceeded'})" )
                conn_result.set_result( False if task_err is None else task_err )
            else:
                _LOGGER.debug( f"[{task_name}]: FINISHED" )
                conn_result.set_result( True )

    async def _async_connect_task_start( self, retries, timeout, status: IntegraClientStatus ) -> asyncio.Future | None:
        if self._connect_task is not None:
            return None

        conn_result: asyncio.Future = self._eventloop.create_future()
        await self._async_set_status( status )
        self._connect_task = asyncio.create_task( self._async_connect_task( retries, timeout, conn_result ), name="connection_task" )
        return conn_result

    async def _async_post_command( self, command: IntegraCommand, data: IntegraCmdData | bytes | None = None ) -> None:
        await self._channel.async_post_command( command, data )

    async def _async_send_command( self, command: IntegraCommand, data: IntegraCmdData | bytes | None = None ) -> IntegraResponse:
        return await self._channel.async_send_command( command, data, self.opts.resp_timeout )

    async def _async_read_parts_data( self, command: IntegraCommand ) -> list[ int ] | None:
        response: IntegraResponse = await self._async_send_command( command )
        if self._check_response( response ) and isinstance( response.data, IntegraCmdUserPartsData ):
            return IntegraCmdPartsData.from_bytes( response.data ).parts
        return None

    async def _async_async_read_zones_data( self, command: IntegraCommand ) -> list[ int ] | None:
        response: IntegraResponse = await self._async_send_command( command, self._request_data_for_zones() )
        if self._check_response( response ):
            return IntegraCmdZonesData.from_bytes( response.data ).zones
        return None

    async def _async_async_read_outputs_data( self, command: IntegraCommand ) -> list[ int ] | None:
        response: IntegraResponse = await self._async_send_command( command, self._request_data_for_outputs() )
        if self._check_response( response ):
            return IntegraCmdOutputsData.from_bytes( response.data ).outputs
        return None

    async def _async_read_doors_data( self, command: IntegraCommand ) -> list[ int ] | None:
        response: IntegraResponse = await self._async_send_command( command )
        if self._check_response( response ):
            return IntegraCmdDoorsData.from_bytes( response.data ).doors
        return None

    def power_monitor_get( self, output_no: int ) -> float:
        if output_no in self._power_monitor:
            return self._power_monitor[ output_no ]
        return 0.0

    def power_monitor_set( self, outputs: dict[ int, float ] | None = None ) -> bool:
        reconfigure = False
        if outputs is None or len( outputs ) == 0:
            if len( self._power_monitor ) != 0:
                self._power_monitor = { }
                reconfigure = True
        else:
            for output_no, interval in outputs.items():
                if output_no in self._power_monitor:
                    if interval > 0:
                        if self._power_monitor[ output_no ] != interval:
                            self._power_monitor[ output_no ] = interval
                            reconfigure = True
                    else:
                        self._power_monitor.pop( output_no )
                        reconfigure = True
                elif interval > 0:
                    self._power_monitor.setdefault( output_no, interval )
                    reconfigure = True

        if reconfigure:
            self._system_monitor_reconfigure()
        return reconfigure

    def temp_monitor_get( self, zone_no: int ) -> float:
        if zone_no in self._temp_monitor:
            return self._temp_monitor[ zone_no ]
        return 0.0

    def temp_monitor_set( self, zones: dict[ int, float ] | None = None ) -> bool:
        reconfigure = False
        if zones is None or len( zones ) == 0:
            if len( self._temp_monitor ) != 0:
                self._temp_monitor = { }
                reconfigure = True
        else:
            for zone_no, interval in zones.items():
                if zone_no in self._temp_monitor:
                    if interval > 0:
                        if self._temp_monitor[ zone_no ] != interval:
                            self._temp_monitor[ zone_no ] = interval
                            reconfigure = True
                    else:
                        self._temp_monitor.pop( zone_no )
                        reconfigure = True
                elif interval > 0:
                    self._temp_monitor.setdefault( zone_no, interval )
                    reconfigure = True

        if reconfigure:
            self._system_monitor_reconfigure()
        return reconfigure

    async def async_read_troubles( self, troubles_block: IntegraTroubles, memory: bool ) -> bytes | None:

        cmds_map: dict[ bool, dict[ IntegraTroubles, IntegraCommand ] ] = {
            False: {
                IntegraTroubles.BLOCK_1: IntegraCommand.READ_TROUBLES_PART1,
                IntegraTroubles.BLOCK_2: IntegraCommand.READ_TROUBLES_PART2,
                IntegraTroubles.BLOCK_3: IntegraCommand.READ_TROUBLES_PART3,
                IntegraTroubles.BLOCK_4: IntegraCommand.READ_TROUBLES_PART4,
                IntegraTroubles.BLOCK_5: IntegraCommand.READ_TROUBLES_PART5,
                IntegraTroubles.BLOCK_6: IntegraCommand.READ_TROUBLES_PART6,
                IntegraTroubles.BLOCK_7: IntegraCommand.READ_TROUBLES_PART7,
                IntegraTroubles.BLOCK_8: IntegraCommand.READ_TROUBLES_PART8,
            },
            True: {
                IntegraTroubles.BLOCK_1: IntegraCommand.READ_TROUBLES_MEMORY_PART1,
                IntegraTroubles.BLOCK_2: IntegraCommand.READ_TROUBLES_MEMORY_PART2,
                IntegraTroubles.BLOCK_3: IntegraCommand.READ_TROUBLES_MEMORY_PART3,
                IntegraTroubles.BLOCK_4: IntegraCommand.READ_TROUBLES_MEMORY_PART4,
                IntegraTroubles.BLOCK_5: IntegraCommand.READ_TROUBLES_MEMORY_PART5,
                IntegraTroubles.BLOCK_6: IntegraCommand.READ_TROUBLES_MEMORY_PART6,
                IntegraTroubles.BLOCK_7: IntegraCommand.READ_TROUBLES_MEMORY_PART7,
                IntegraTroubles.BLOCK_8: IntegraCommand.READ_TROUBLES_MEMORY_PART8,
            }
        }
        command: IntegraCommand = cmds_map[ memory ][ troubles_block ]
        response: IntegraResponse = await self._async_send_command( command )
        if self._check_response( response ):
            return response.data
        return None

    # 0x00
    async def async_read_zones_violation( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_VIOLATION )

    # 0x01
    async def async_read_zones_tamper( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_TAMPER )

    # 0x02
    async def async_read_zones_alarm( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_ALARM )

    # 0x03
    async def async_read_zones_tamper_alarm( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_TAMPER_ALARM )

    # 0x04
    async def async_read_zones_alarm_memory( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_ALARM_MEMORY )

    # 0x05
    async def async_read_zones_tamper_alarm_memory( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_TAMPER_ALARM_MEMORY )

    # 0x06
    async def async_read_zones_bypass( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_BYPASS )

    # 0x07
    async def async_read_zones_no_violation_trouble( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_NO_VIOLATION_TROUBLE )

    # 0x08
    async def async_read_zones_long_violation_trouble( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_LONG_VIOLATION_TROUBLE )

    # 0x09
    async def async_read_parts_armed_suppressed( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ARMED_SUPPRESSED )

    # 0x0A
    async def async_read_parts_armed_really( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ARMED_REALLY )

    # 0x0B
    async def async_read_parts_armed_mode2( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ARMED_MODE_2 )

    # 0x0C
    async def async_read_parts_armed_mode3( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ARMED_MODE_3 )

    # 0x0D
    async def async_read_parts_1st_code_entered( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_1ST_CODE_ENTERED )

    # 0x0E
    async def async_read_parts_entry_time( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ENTRY_TIME )

    # 0x0F
    async def async_read_parts_exit_time_above10( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_EXIT_TIME_ABOVE_10 )

    # 0x10
    async def async_read_parts_exit_time_below10( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_EXIT_TIME_BELOW_10 )

    # 0x11
    async def async_read_parts_temporary_blocked( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_TEMP_BLOCKED )

    # 0x12
    async def async_read_parts_blocked_for_guard( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_BLOCKED_FOR_GUARD )

    # 0x13
    async def async_read_parts_alarm( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ALARM )

    # 0x14
    async def async_read_parts_fire_alarm( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_FIRE_ALARM )

    # 0x15
    async def async_read_parts_alarm_memory( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ALARM_MEMORY )

    # 0x16
    async def async_read_parts_fire_alarm_memory( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_FIRE_ALARM_MEMORY )

    # 0x17
    async def async_read_outputs_state( self ) -> list[ int ] | None:
        return await self._async_async_read_outputs_data( IntegraCommand.READ_OUTPUTS_STATE )

    # 0x18
    async def async_read_doors_opened( self ) -> list[ int ] | None:
        return await self._async_read_doors_data( IntegraCommand.READ_DOORS_OPENED )

    # 0x19
    async def async_read_doors_opened_long( self ) -> list[ int ] | None:
        return await self._async_read_doors_data( IntegraCommand.READ_DOORS_OPENED_LONG )

    # 0x1A
    async def async_read_rtc_and_status( self ) -> IntegraCmdRtcData | None:
        response: IntegraResponse = await  self._async_send_command( IntegraCommand.READ_RTC_AND_STATUS )
        if self._check_response( response ):
            return IntegraCmdRtcData.from_bytes( response.data )
        return None

    # 0x1B READ: troubles 1
    async def async_read_troubles1( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_1, False )

    # 0x1C READ: troubles 2
    async def async_read_troubles2( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_2, False )

    # 0x1D READ: troubles 3
    async def async_read_troubles3( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_3, False )

    # 0x1E READ: troubles 4
    async def async_read_troubles4( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_4, False )

    # 0x1F READ: troubles 5
    async def async_read_troubles5( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_5, False )

    # 0x20 READ: troubles memory 1
    async def async_read_troubles_memory1( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_1, True )

    # 0x21 READ: troubles memory 2
    async def async_read_troubles_memory2( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_2, True )

    # 0x22 READ: troubles memory 3
    async def async_read_troubles_memory3( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_3, True )

    # 0x23 READ: troubles memory 4
    async def async_read_troubles_memory4( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_4, True )

    # 0x24 READ: troubles memory 5
    async def async_read_troubles_memory5( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_5, True )

    # 0x25
    async def async_read_parts_with_violated_zones( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_WITH_VIOLATED_ZONES )

    # 0x26
    async def async_read_zones_isolate( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_ISOLATE )

    # 0x27
    async def async_read_parts_with_verified_alarms( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_WITH_VERIFIED_ALARMS )

    # 0x28
    async def async_read_zones_masked( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_MASKED )

    # 0x29
    async def async_read_zones_masked_memory( self ) -> list[ int ] | None:
        return await self._async_async_read_zones_data( IntegraCommand.READ_ZONES_MASKED_MEMORY )

    # 0x2A
    async def async_read_parts_armed_mode1( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_ARMED_MODE_1 )

    # 0x2B
    async def async_read_parts_with_warning_alarms( self ) -> list[ int ] | None:
        return await self._async_read_parts_data( IntegraCommand.READ_PARTS_WITH_WARNING_ALARMS )

    # 0x2C READ: troubles 6
    async def async_read_troubles6( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_6, False )

    # 0x2D READ: troubles 7
    async def async_read_troubles7( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_7, False )

    # 0x2E READ: troubles memory 6
    async def async_read_troubles_memory6( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_6, True )

    # 0x2F READ: troubles memory 7
    async def async_read_troubles_memory7( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_7, True )

    # 0x30 READ: troubles 8
    async def async_read_troubles8( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_8, False )

    # 0x31 READ: troubles memory 8
    async def async_read_troubles_memory8( self ) -> bytes:
        return await self.async_read_troubles( IntegraTroubles.BLOCK_8, True )

    # 0x7B
    async def async_read_output_power( self, output_no: int ) -> IntegraCmdOutputPower | None:
        cmd_data = IntegraCmdOutputData( output_no )
        response: IntegraResponse = await self._async_send_command( IntegraCommand.READ_OUTPUT_POWER, cmd_data )
        if self._check_response( response ):
            return IntegraCmdOutputPower.from_bytes( response.data )
        return None

    # 0x7C READ: module version
    async def async_read_module_version( self ) -> IntegraCmdModuleVersionData | None:
        response: IntegraResponse = await self._async_send_command( IntegraCommand.READ_MODULE_VERSION )
        if self._check_response( response ):
            return IntegraCmdModuleVersionData.from_bytes( response.data )
        return None

    # 0x7D READ: output temperature
    async def async_read_zone_temperature( self, zone_no: int ) -> IntegraCmdZoneTemp | None:
        cmd_data = IntegraCmdZoneData( zone_no )
        cmd_data.to_bytes()
        response: IntegraResponse = await self._async_send_command( IntegraCommand.READ_ZONE_TEMPERATURE, cmd_data )
        if self._check_response( response ):
            return IntegraCmdZoneTemp.from_bytes( response.data )
        return None

    # 0x7E READ: integra version
    async def async_read_integra_version( self ) -> IntegraCmdVersionData | None:
        response: IntegraResponse = await self._async_send_command( IntegraCommand.READ_INTEGRA_VERSION )
        if self._check_response( response ):
            return IntegraCmdVersionData.from_bytes( response.data )
        return None

    # 0x7F READ: system changes
    async def async_read_system_changes( self ) -> list[ IntegraCommand ]:

        result: list[ IntegraCommand ] = [ ]

        cmd_data = bytes( 0 ) if not self.support_troubles67 else bytes( 2 ) if self.support_troubles8 else bytes( 1 )

        response: IntegraResponse = await self._async_send_command( IntegraCommand.READ_SYSTEM_CHANGES, IntegraCmdRawData( cmd_data ) )

        if self._check_response( response ):
            result = IntegraCommandHelper.cmds_from_bytes( response.data, self._get_cmd_list_len() )

        return result

    # 0x7F READ: system changes - special version: setup state changes to monitor
    async def _async_system_changes_monitor( self, changed_cmds: list[ IntegraCommand ] | None, rcvd_cmds: list[ IntegraCommand ] | None = None ) -> bool:

        cmd_list_len = self._get_cmd_list_len()

        cmd_data = IntegraCmdRawData( (IntegraCommandHelper.cmds_to_bytes( changed_cmds, cmd_list_len ) +
                                       IntegraCommandHelper.cmds_to_bytes( rcvd_cmds, cmd_list_len )) )

        response: IntegraResponse = await self._async_send_command( IntegraCommand.READ_SYSTEM_CHANGES, cmd_data )
        return self._check_response( response )

    async def async_notify_events_setup( self, changed_events: list[ IntegraNotifyEvent ] | None, rcvd_events: list[ IntegraNotifyEvent ] | None = None ) -> bool:
        if await self._async_system_changes_monitor( IntegraNotifyEvent.to_commands( changed_events ), IntegraNotifyEvent.to_commands( rcvd_events ) ):
            self._changed_events = changed_events if changed_events is not None else [ ]
            self._rcvd_events = rcvd_events if rcvd_events is not None else [ ]
            return True
        return False

    # 0x80 CONTROL: arm in mode
    # 0x81, 0x82, 0x83, 0xA0, 0xA1, 0xA2, 0xA3
    async def async_ctrl_arm( self, mode: IntegraArmMode, partitions: list[ int ], force: bool = False, without_bypass_and_delay: bool = False, user_code: str = "" ) -> bool:
        cmd_value = IntegraCommand( (IntegraCommand.EXEC_FORCE_ARM_MODE_0 if force else IntegraCommand.EXEC_ARM_MODE_0).value + mode.value )
        without_bypass_and_delay = without_bypass_and_delay if self.module_version.caps & IntegraModuleCaps.MODULE_CAP_ARM_NO_BYPASS else None
        cmd_data = IntegraCmdUserPartsArmData( self.opts.get_user_code( user_code ), self.opts.prefix_code, partitions, without_bypass_and_delay )
        response = await self._async_send_command( cmd_value, cmd_data )
        return self._check_response( response )

    # 0x84 CONTROL: disarm
    async def async_ctrl_disarm( self, partitions: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserPartsData( self.opts.get_user_code( user_code ), self.opts.prefix_code, partitions )
        response = await self._async_send_command( IntegraCommand.EXEC_DISARM, cmd_data )
        return self._check_response( response )

    # 0x85 CONTROL: clear alarm
    async def async_ctrl_clear_alarm( self, partitions: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserPartsData( self.opts.get_user_code( user_code ), self.opts.prefix_code, partitions )
        response = await self._async_send_command( IntegraCommand.EXEC_CLEAR_ALARM, cmd_data )
        return self._check_response( response )

    # 0xA0, 0xA1, 0xA2, 0xA3 => GO TO 0x80

    # 0x86 CONTROL: zones bypass
    async def async_ctrl_zones_bypass_set( self, zones: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserZonesData( self.opts.get_user_code( user_code ), self.opts.prefix_code, zones )
        response = await self._async_send_command( IntegraCommand.EXEC_ZONES_BYPASS_SET, cmd_data )
        return self._check_response( response )

    # 0x87 CONTROL: zones bypass unset
    async def async_ctrl_zones_bypass_unset( self, zones: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserZonesData( self.opts.get_user_code( user_code ), self.opts.prefix_code, zones )
        response = await self._async_send_command( IntegraCommand.EXEC_ZONES_BYPASS_UNSET, cmd_data )
        return self._check_response( response )

    # 0x88 CONTROL: outputs on
    async def async_ctrl_outputs_on( self, outputs: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserOutputsData( self.opts.get_user_code( user_code ), self.opts.prefix_code, outputs, 256 if self.support_32bytes else 128 )
        response = await self._async_send_command( IntegraCommand.EXEC_OUTPUTS_ON, cmd_data )
        return self._check_response( response )

    # 0x89 CONTROL: outputs off
    async def async_ctrl_outputs_off( self, outputs: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserOutputsData( self.opts.get_user_code( user_code ), self.opts.prefix_code, outputs, 256 if self.support_32bytes else 128 )
        response = await self._async_send_command( IntegraCommand.EXEC_OUTPUTS_OFF, cmd_data )
        return self._check_response( response )

    # 0x8A CONTROL: door open
    async def async_ctrl_door_open( self, expanders: list[ int ] | None, outputs: list[ int ] | None = None, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserOutputsExpandersData( self.opts.get_user_code( user_code ), self.opts.prefix_code, expanders, outputs, 256 if self.support_32bytes else 128 )
        response = await self._async_send_command( IntegraCommand.EXEC_OPEN_DOOR, cmd_data )
        return self._check_response( response )

    # 0x8B CONTROL: trouble memory clear
    async def async_ctrl_trouble_mem_clear( self, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserCodeData( self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.EXEC_CLEAR_TROUBLE_MEMORY, cmd_data )
        return self._check_response( response )

    # 0x8C CONTROL: read event
    async def _async_ctrl_read_event( self, event_index: int, event_source: IntegraEventSource ) -> IntegraEventRecData | None:
        cmd_data = IntegraCmdEventRecData( event_index )
        response = await self._async_send_command( IntegraCommand.EXEC_READ_EVENT, cmd_data )
        if response is not None and response.success:
            if event_source == IntegraEventSource.STANDARD:
                return IntegraEventRecStdData.from_bytes( response.data )
            elif event_source == IntegraEventSource.GRADE2:
                return IntegraEventRecGradeData.from_bytes( response.data )
        return None

    # 0x8C CONTROL: read event STANDARD
    # TO IMPLEMENT
    async def async_ctrl_read_std_event( self, event: IntegraEventRecData | None = None ) -> IntegraEventRecData | None:
        event_index = INTEGRA_EVENT_STD_LAST if event is None else event.index
        result = await self._async_ctrl_read_event( event_index, IntegraEventSource.STANDARD )
        if result is None or result.no_more:
            return None
        return result

    # 0x8C CONTROL: read event GRADE2
    # TO IMPLEMENT
    async def async_ctrl_read_grade_event( self, event: IntegraEventRecData | None = None ) -> IntegraEventRecData | None:
        event_index = INTEGRA_EVENT_GRADE_LAST if event is None else event.index
        result = await self._async_ctrl_read_event( event_index, IntegraEventSource.GRADE2 )
        if result is None or result.no_more:
            return None
        return result

    # 0x8D CONTROL: enter 1st code
    async def async_ctrl_enter_1st_code( self, partitions: list[ int ], action: Integra1stCodeAction, validity_period: int, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserParts1stCodeData( self.opts.get_user_code( user_code ), self.opts.prefix_code, partitions, action, validity_period )
        response = await self._async_send_command( IntegraCommand.EXEC_ENTER_1ST_CODE, cmd_data )
        return self._check_response( response )

    # 0x8E CONTROL: set RTC clock
    async def async_ctrl_set_rtc_clock( self, date: datetime | None = None, user_code: str = "" ) -> bool:
        if date is None:
            date = datetime.now()
        cmd_data = IntegraCmdUserSetRtcData( self.opts.get_user_code( user_code ), self.opts.prefix_code, date )
        response = await self._async_send_command( IntegraCommand.EXEC_SET_RTC_CLOCK, cmd_data )
        return self._check_response( response )

    # 0x8F CONTROL: get event text
    # TO IMPLEMENT
    async def async_ctrl_get_event_text( self, event_code_full: int, show_long: bool = True ) -> IntegraEventTextData | None:
        cmd_data = IntegraCmdEventTextData( event_code_full, show_long )
        response = await self._async_send_command( IntegraCommand.EXEC_GET_EVENT_TEXT, cmd_data )
        if response is None or not response.success:
            return None
        result = IntegraEventTextData.from_bytes( response.data )
        return result

    # 0x90 CONTROL: zones isolate
    async def async_ctrl_zones_isolate( self, zones: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserZonesData( self.opts.get_user_code( user_code ), self.opts.prefix_code, zones )
        response = await self._async_send_command( IntegraCommand.EXEC_ZONES_ISOLATE, cmd_data )
        return self._check_response( response )

    # 0x91 CONTROL: outputs switch
    async def async_ctrl_outputs_switch( self, outputs: list[ int ], user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserOutputsData( self.opts.get_user_code( user_code ), self.opts.prefix_code, outputs, 256 if self.support_32bytes else 128 )
        response = await self._async_send_command( IntegraCommand.EXEC_OUTPUTS_SWITCH, cmd_data )
        return self._check_response( response )

    # 0xE0 USERS: read user self-info
    async def async_user_read_self( self, user_code: str = "" ) -> IntegraUserSelf | None:
        cmd_data = IntegraCmdUserCodeData( self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_READ_SELF_INFO, cmd_data )
        if self._check_response( response ):
            return IntegraUserSelf.from_bytes( response.data )
        return None

    # 0xE1 USERS: read user other
    async def async_user_read_other( self, user_no: int, user_code: str = "" ) -> IntegraUserOther | None:
        cmd_data = IntegraCmdUserCodeNoData( user_no, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_READ_OTHER_INFO, cmd_data )
        if self._check_response( response ):
            return IntegraUserOther.from_bytes( response.data )
        return None

    # 0xE2 USERS: read users list
    async def async_user_read_users_list( self, user_no: int, user_code: str = "" ) -> IntegraUsersList | None:
        cmd_data = IntegraCmdUserCodeNoData( user_no, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_READ_USERS_LIST, cmd_data )
        if self._check_response( response ):
            return IntegraUsersList.from_bytes( response.data )
        return None

    # 0xE3 USERS: read users locks
    async def async_user_read_user_locks( self, user_no: int, user_code: str = "" ) -> IntegraUserLocks | None:
        cmd_data = IntegraCmdUserCodeNoData( user_no, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_READ_USER_LOCKS, cmd_data )
        if self._check_response( response ):
            return IntegraUserLocks.from_bytes( response.data )
        return None

    # 0xE4 USERS: write user locks
    async def async_user_write_user_locks( self, user_locks, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserSetUserLocksData( user_locks, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_WRITE_USER_LOCKS, cmd_data )
        if self._check_response( response ):
            return True
        return False

    # 0xE5 USERS: remove user
    async def async_user_remove( self, user_no: int, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserCodeNoData( user_no, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_REMOVE, cmd_data )
        if self._check_response( response ):
            return True
        return False

    # 0xE6 USERS: create user
    async def async_user_create( self, user: IntegraUser, user_code: str = "" ):
        cmd_data = IntegraCmdUserCodeUserData( user, True, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_CREATE, cmd_data )
        if self._check_response( response ):
            return True
        return False

    # 0xE7 USERS: change user
    async def async_user_change( self, user: IntegraUser, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserCodeUserData( user, False, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_CHANGE, cmd_data )
        if self._check_response( response ):
            return True
        return False

    # 0xE8 USERS: user DALLAS/proximity card/key fob managing
    async def async_user_read_card_list( self, user_code: str = "" ) -> IntegraUserDevMgmtList | None:
        cmd_data = IntegraCmdUserDevMgmtData( IntegraUserDeviceMgmtFunc.READ_LIST, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return IntegraUserDevMgmtList.from_bytes( response.data )
        return None

    async def async_user_read_proximity_card( self, user_no: int, user_code: str = "" ) -> IntegraUserProximityCard | None:
        cmd_data = IntegraCmdUserDevMgmtUserData( user_no, IntegraUserDeviceMgmtFunc.READ_PROXIMITY_CARD, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return IntegraUserProximityCard.from_bytes( response.data )
        return None

    async def async_user_write_proximity_card( self, card: IntegraUserProximityCard, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserDevMgmtDeviceData( card, IntegraUserDeviceMgmtFunc.WRITE_PROXIMITY_CARD, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return True
        return False

    async def async_user_read_dallas_dev( self, user_no: int, user_code: str = "" ) -> IntegraUserDallasDev | None:
        cmd_data = IntegraCmdUserDevMgmtUserData( user_no, IntegraUserDeviceMgmtFunc.READ_DALLAS_DEV, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return IntegraUserDallasDev.from_bytes( response.data )
        return None

    async def async_user_write_dallas_dev( self, dev: IntegraUserDallasDev, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserDevMgmtDeviceData( dev, IntegraUserDeviceMgmtFunc.WRITE_DALLAS_DEV, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return True
        return False

    async def async_user_read_intrx_key_fob( self, user_no: int, user_code: str = "" ) -> IntegraUserIntRxKeyFob | None:
        cmd_data = IntegraCmdUserDevMgmtUserData( user_no, IntegraUserDeviceMgmtFunc.READ_INTRX_KEY_FOB, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return IntegraUserIntRxKeyFob.from_bytes( response.data )
        return None

    async def async_user_write_intrx_key_fob( self, key_fob: IntegraUserIntRxKeyFob, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserDevMgmtDeviceData( key_fob, IntegraUserDeviceMgmtFunc.WRITE_INTRX_KEY_FOB, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return True
        return False

    async def async_user_read_abax_key_fob( self, user_no: int, user_code: str = "" ) -> IntegraUserAbaxKeyFob | None:
        cmd_data = IntegraCmdUserDevMgmtUserData( user_no, IntegraUserDeviceMgmtFunc.READ_ABAX_KEY_FOB, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return IntegraUserAbaxKeyFob.from_bytes( response.data )
        return None

    async def async_user_write_abax_key_fob( self, key_fob: IntegraUserAbaxKeyFob, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserDevMgmtDeviceData( key_fob, IntegraUserDeviceMgmtFunc.WRITE_ABAX_KEY_FOB, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_MANAGE_DEVS, cmd_data )
        if self._check_response( response ) and self._check_response_user( response.data ):
            return True
        return False

    # 0xE9 USERS: change user code
    async def async_user_change_user_code( self, user_code_new: str, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserCodeNewCodeUserData( user_code_new, self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_CHANGE_CODE, cmd_data )
        if self._check_response( response ):
            return True
        return False

    # 0xEA USERS: change user tel. code
    async def async_user_change_phone_code( self, phone_code_new: str, user_code: str = "" ) -> bool:
        cmd_data = IntegraCmdUserCodeNewCodePhoneData( phone_code_new.strip( " " ), self.opts.get_user_code( user_code ), self.opts.prefix_code )
        response = await self._async_send_command( IntegraCommand.USER_CHANGE_PHONE_CODE, cmd_data )
        if self._check_response( response ):
            return True
        return False

    # 0xEE read device name
    async def _async_read_element_data( self, element_no: int, element_class: type[ IntegraElement ], expect_error_codes: list[ IntegraResponseErrorCode ] | None = None ) -> IntegraElement | None:
        cmd_data = IntegraCmdReadElementData( element_class, element_no )
        response: IntegraResponse = await self._async_send_command( IntegraCommand.ELEMENT_READ_NAME, cmd_data )
        if response.success:
            element = element_class.from_bytes( response.data )
            return element
        return element_class.empty_element( element_no ) if expect_error_codes is not None and response.error_code in expect_error_codes else None

    # 0xEE / 0
    async def async_read_part_data( self, part_no: int ) -> IntegraPartElement | None:
        return await self._async_read_element_data( part_no, IntegraPartElement )

    # 0xEE / 1
    async def async_read_zone_data( self, zone_no: int ) -> IntegraZoneElement | None:
        return await self._async_read_element_data( zone_no, IntegraZoneElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 2 - user
    async def async_read_user_data( self, user_no: int ) -> IntegraUserElement | None:
        return await self._async_read_element_data( user_no, IntegraUserElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 2 - admin
    async def async_read_admin_data( self, admin_no: int ) -> IntegraAdminElement | None:
        return await self._async_read_element_data( admin_no, IntegraAdminElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 3 - expander
    async def async_read_expander_data( self, expander_no: int ) -> IntegraExpanderElement | None:
        return await self._async_read_element_data( expander_no, IntegraExpanderElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 3 - manipulator
    async def async_read_manipulator_data( self, manipulator_no: int ) -> IntegraManipulatorElement | None:
        return await self._async_read_element_data( manipulator_no, IntegraManipulatorElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 4
    async def async_read_output_data( self, output_no: int ) -> IntegraOutputElement | None:
        return await self._async_read_element_data( output_no, IntegraOutputElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 5
    async def async_read_zone_with_parts_data( self, zone_no: int ) -> IntegraZoneElement | None:
        return await self._async_read_element_data( zone_no, IntegraZoneWithPartsElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 6
    async def async_read_timer_data( self, timer_no: int ) -> IntegraTimerElement | None:
        return await self._async_read_element_data( timer_no, IntegraTimerElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 7
    async def async_read_phone_data( self, phone_no: int ) -> IntegraPhoneElement | None:
        return await self._async_read_element_data( phone_no, IntegraPhoneElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 15
    async def async_read_object_data( self, object_no: int ) -> IntegraObjectElement | None:
        return await self._async_read_element_data( object_no, IntegraObjectElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 16
    async def async_read_part_with_object_data( self, part_no: int ) -> IntegraPartWithObjElement | None:
        return await self._async_read_element_data( part_no, IntegraPartWithObjElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 17
    async def async_read_output_with_duration_data( self, output_no: int ) -> IntegraOutputWithDurationElement | None:
        return await self._async_read_element_data( output_no, IntegraOutputWithDurationElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 18
    async def async_read_part_with_obj_opts_data( self, part_no: int ) -> IntegraPartWithObjOptsElement | None:
        return await self._async_read_element_data( part_no, IntegraPartWithObjOptsElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    # 0xEE / 19
    async def async_read_part_with_obj_opts_deps_data( self, part_no: int ) -> IntegraPartWithObjOptsDepsElement | None:
        return await self._async_read_element_data( part_no, IntegraPartWithObjOptsDepsElement, [ IntegraResponseErrorCode.OTHER_ERROR ] )

    async def async_connect( self, retries: int = 0, timeout: float | None = None ) -> bool:

        timeout = self.opts.conn_timeout if timeout is None else timeout
        if self._channel.connected:
            return True

        conn_result = await self._async_connect_task_start( retries, timeout, IntegraClientStatus.CONNECTING )
        if conn_result is not None:
            result = await asyncio.wait_for( conn_result, None )
            if isinstance( result, Exception ):
                raise result
        return self._status == IntegraClientStatus.CONNECTED

    async def async_disconnect( self ) -> bool:
        if self._connect_task is not None:
            await self._async_set_status( IntegraClientStatus.DISCONNECTING )
            connect_task = self._connect_task
            connect_task.cancel()
            try:
                await connect_task
            except Exception as err:
                _LOGGER.debug( f"connection_task await, {err}" )
            finally:
                await self._channel.async_disconnect()
                await self._async_set_status( IntegraClientStatus.DISCONNECTED )
            return True

        if not self._channel.connected:
            return True

        await self._async_set_status( IntegraClientStatus.DISCONNECTING )
        await self._channel.async_disconnect()
        return True

    async def async_build_event_cache( self ):

        def index_of_event( code: int, lookup_list: list ) -> int:
            idx = 0
            for item in lookup_list:
                if item[ "code" ] == code:
                    return idx
                idx += 1

            return -1

        events: list[ dict ] = [ ]
        for event_code in range( 1024 ):
            for event_code_full in [ event_code, event_code | 0x400 ]:
                for show_long in [ True, False ]:
                    event_txt: IntegraEventTextData = await self.async_ctrl_get_event_text( event_code_full, show_long )
                    if event_txt is not None and event_txt.text.rstrip( " " ) != "":
                        event_json = event_txt.to_json()
                        events.append( event_json )

        events_cache = {
            "version": f"{self.integra_version.major}.{self.integra_version.minor:2d}",
            "date": f"{self.integra_version.date:%Y-%m-%d}",
            "lang": self.integra_version.lang.name.lower(),
            "events": [ ]
        }
        for event in events:
            index = index_of_event( event[ "code" ], events_cache[ "events" ] )
            show_long = event[ "show_long" ]
            text = event[ "text" ]
            if index != -1:
                events_cache[ "events" ][ index ].update( {
                    ("text_long" if show_long else "text_short"): text
                } )
            else:
                event.pop( "show_long" )
                event.pop( "text" )
                event.update( { "text_long": (text if show_long else ""), "text_short": ("" if show_long else text) } )
                events_cache[ "events" ].append( event )

        filename: str = f"{os.path.dirname( __file__ )}{os.path.sep}events{os.path.sep}events_{self.integra_version.lang.name.lower()}.json"
        with open( filename, "w" ) as f:
            f.write( json.dumps( events_cache, indent=2 ) )
