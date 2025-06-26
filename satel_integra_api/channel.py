import os
import traceback
import logging
import asyncio

from datetime import datetime
from asyncio import CancelledError as AsyncCancelledError, Lock, Task, TimeoutError as AsyncTimeoutError
from asyncio.events import AbstractEventLoop
from enum import IntEnum, StrEnum
from typing import Any, Awaitable, Callable
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .base import IntegraEntity, IntegraError
from .const import (
    DEFAULT_CODE_PAGE,
    DEFAULT_CONN_TIMEOUT,
    DEFAULT_KEEP_ALIVE,
    DEFAULT_RESP_TIMEOUT,
    DEBUG_SHOW_REQUESTS,
    DEBUG_SHOW_REQUESTS_RAW,
    DEBUG_SHOW_REQUESTS_ENC,
    DEBUG_SHOW_RESPONSES,
    DEBUG_SHOW_RESPONSES_TIME,
    DEBUG_SHOW_RESPONSES_RAW,
    DEBUG_SHOW_RESPONSES_ENC,
    FRAME_SYNC,
    FRAME_SYNC_ESC,
    FRAME_SYNC_END
)
from .commands import IntegraCommand, IntegraCmdData, IntegraCmdReadElementData
from .elements import IntegraZoneElement
from .messages import IntegraRequest, IntegraResponse, IntegraResponseErrorCode
from .tools import IntegraHelper

_LOGGER = logging.getLogger( __name__ )


class IntegraChannelEvent( IntEnum ):
    CONNECTED = 1,
    DISCONNECTED = 2,
    NOTIFICATION = 3,


IntegraChannelType = 'IntegraChannel'
IntegraChannelEventCallback = Callable[ [ IntegraChannelType, IntegraChannelEvent, Any ], Awaitable ] | None


class IntegraChannelStats( IntegraEntity ):

    def __init__( self ):
        super().__init__()
        self._date = datetime.min
        self._rx_bytes = 0
        self._rx_enc_bytes = 0
        self._tx_bytes = 0
        self._tx_enc_bytes = 0

    @property
    def rx_bytes( self ) -> int:
        return self._rx_bytes

    @property
    def tx_bytes( self ) -> int:
        return self._tx_bytes

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Uptime": f"{(datetime.now() - self._date).seconds}",
            "RX": f"{self._rx_bytes} / {self._rx_enc_bytes}",
            "TX": f"{self._tx_bytes} / {self._tx_enc_bytes}",
        } )

    def restart( self ):
        self._date = datetime.now()
        self._rx_bytes = 0
        self._rx_enc_bytes = 0
        self._tx_bytes = 0
        self._tx_enc_bytes = 0

    def update_rx_bytes( self, delta: int = 1 ):
        self._rx_bytes += delta

    def update_rx_enc_bytes( self, delta: int = 1 ):
        self._rx_enc_bytes += delta

    def update_tx_bytes( self, delta: int = 1 ):
        self._tx_bytes += delta

    def update_tx_enc_bytes( self, delta: int = 1 ):
        self._tx_enc_bytes += delta


class IntegraChannelErrorCode( IntEnum ):
    NOT_CONNECTED = 0
    CONN_TIMEOUT = 1
    CONN_REFUSED = 2
    READ_ERROR = 3
    WRITE_ERROR = 4
    INVALID_ENCRYPTION_KEY = 5
    REMOTE_CLOSED = 6
    REMOTE_BUSY = 7


class IntegraChannelError( IntegraError ):

    def __init__( self, channel_id: str, error_code: IntegraChannelErrorCode, exception: BaseException | str | None = None ):
        super().__init__()
        self._channel_id: str = channel_id
        self._error_code: IntegraChannelErrorCode = error_code
        self._exception: BaseException | str | None = exception

    @property
    def channel_id( self ) -> str:
        return self._channel_id

    @property
    def error_code( self ) -> IntegraChannelErrorCode:
        return self._error_code

    @property
    def exception( self ) -> BaseException | str | None:
        return self._exception

    @property
    def message( self ) -> str:
        if self._error_code == IntegraChannelErrorCode.NOT_CONNECTED:
            return f"Remote endpoint {self.channel_id} is not connected."
        elif self._error_code == IntegraChannelErrorCode.CONN_TIMEOUT:
            return f"Connection to remote endpoint {self.channel_id} cannot be established{self._get_exception_info()}"
        elif self._error_code == IntegraChannelErrorCode.CONN_REFUSED:
            return f"Connection to remote endpoint {self.channel_id} refused{self._get_exception_info()}"
        elif self._error_code == IntegraChannelErrorCode.READ_ERROR:
            return f"Error reading data from remote endpoint {self.channel_id}{self._get_exception_info()}"
        elif self._error_code == IntegraChannelErrorCode.WRITE_ERROR:
            return f"Error writing data to remote endpoint {self.channel_id}{self._get_exception_info()}"
        elif self._error_code == IntegraChannelErrorCode.INVALID_ENCRYPTION_KEY:
            return f"Invalid encryption key for remote endpoint {self.channel_id}{self._get_exception_info()}"
        elif self._error_code == IntegraChannelErrorCode.REMOTE_CLOSED:
            return f"Remote endpoint {self.channel_id} closed connection{self._get_exception_info()}"
        elif self._error_code == IntegraChannelErrorCode.REMOTE_BUSY:
            return f"Remote endpoint {self.channel_id} returned busy{self._get_exception_info()}"

        return f"Remote endpoint {self.channel_id} returned error {self._error_code.name}{self._get_exception_info()}"

    def _get_exception_info( self ) -> str:
        if self.exception is not None:
            if isinstance( self.exception, BaseException ):
                exception_msg = f"{self.exception}"
                if exception_msg != "":
                    return f" ({self.exception.__class__.__name__}: {self.exception})"
                return f" ({self.exception.__class__.__name__})"
            return f" ({self.exception})"
        return ""


class IntegraChannel:
    class CloseSource( StrEnum ):
        CONNECT = "connect"
        CONN_TASK = "conn_task"
        DISCONNECT = "disconnect"
        PING_TASK = "ping_task"
        READ_TASK = "read_task"
        REQUEST = "request"

    class EncryptionHandler( IntegraEntity ):
        _BLOCK_LENGTH = 16
        next_id_s: int = 0

        @staticmethod
        def _get_cipher( key: str | None ) -> Cipher | None:

            if key is None or key == "":
                return None

            key_bytes = bytes( key, "ascii" )
            key_data = [ 0 ] * 24
            for i in range( 12 ):
                key_data[ i ] = key_data[ i + 12 ] = key_bytes[ i ] if i < len( key_bytes ) else 0x20

            return Cipher( algorithms.AES( bytes( key_data ) ), modes.ECB() )

        def __init__( self, channel: 'IntegraChannel', integration_key: str | None = None ):
            super().__init__()
            self._channel = channel
            self._cipher = self._get_cipher( integration_key )

            self._rolling_counter: int = 0
            self._id_r: int = 0
            self._id_s: int = IntegraChannel.EncryptionHandler.next_id_s
            IntegraChannel.EncryptionHandler.next_id_s += 1

        @property
        def channel( self ) -> 'IntegraChannel':
            return self._channel

        @property
        def channel_id( self ) -> str:
            return self._channel.channel_id

        @staticmethod
        def _data_blocks( data: bytes, block_len: int ):
            return [ data[ i:i + block_len ] for i in range( 0, len( data ), block_len ) ]

        def _data_decrypt( self, data: bytes ) -> bytes:

            decrypted_data = [ ]
            decryptor = self._cipher.decryptor()
            encryptor = self._cipher.encryptor()
            cv = list( encryptor.update( bytes( [ 0 ] * self._BLOCK_LENGTH ) ) )
            for block in self._data_blocks( data, self._BLOCK_LENGTH ):
                temp = list( block )
                c = list( block )
                if len( block ) == self._BLOCK_LENGTH:
                    c = list( decryptor.update( bytes( c ) ) )
                    c = [ a ^ b for a, b in zip( c, cv ) ]
                    cv = list( temp )
                else:
                    cv = list( encryptor.update( bytes( cv ) ) )
                    c = [ a ^ b for a, b in zip( c, cv ) ]
                decrypted_data += c
            return bytes( decrypted_data )

        def _data_encrypt( self, data: bytes ) -> bytes:
            if len( data ) < self._BLOCK_LENGTH:
                data += b'\x00' * (self._BLOCK_LENGTH - len( data ))
            encrypted_data = [ ]
            encryptor = self._cipher.encryptor()
            cv = list( encryptor.update( bytes( [ 0 ] * self._BLOCK_LENGTH ) ) )
            for block in self._data_blocks( data, self._BLOCK_LENGTH ):
                p = list( block )
                if len( block ) == self._BLOCK_LENGTH:
                    p = [ a ^ b for a, b in zip( p, cv ) ]
                    p = list( encryptor.update( bytes( p ) ) )
                    cv = list( p )
                else:
                    cv = list( encryptor.update( bytes( cv ) ) )
                    p = [ a ^ b for a, b in zip( p, cv ) ]
                encrypted_data += p
            return bytes( encrypted_data )

        def _write_data_with_pdu( self, data: bytes ) -> bytes:
            pdu = (
                    os.urandom( 2 ) +
                    self._rolling_counter.to_bytes( 2, byteorder="big" ) +
                    self._id_s.to_bytes( 1, byteorder="big" ) +
                    self._id_r.to_bytes( 1, byteorder="big" )
            )
            self._rolling_counter += 1
            self._rolling_counter &= 0xFFFF
            self._id_s = pdu[ 4 ]

            return self._data_encrypt( pdu + data )

        def _read_data_from_pdu( self, pdu: bytes ) -> bytes:
            decrypted_pdu = self._data_decrypt( pdu )
            header = decrypted_pdu[ :6 ]
            data = decrypted_pdu[ 6: ]
            self._id_r = header[ 4 ]
            if (self._id_s & 0xFF) != decrypted_pdu[ 5 ]:
                raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.INVALID_ENCRYPTION_KEY, f"Incorrect value of ID_S, received 0x{decrypted_pdu[ 5 ]:02x}, expected 0x{self._id_s:02x}" )
            return bytes( data )

        async def _async_read_encrypted( self ) -> bytes:

            read_chunk = await self.channel._async_channel_read( 1 )
            self._channel._stats.update_rx_enc_bytes( 1 )
            if len( read_chunk ) == 0 or read_chunk[ 0 ] == 0:
                raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.REMOTE_CLOSED )

            size: int = read_chunk[ 0 ]
            pdu = await self.channel._async_channel_read( size )
            if DEBUG_SHOW_RESPONSES_ENC:
                _LOGGER.debug( f"_async_read_encrypted_request[{self.channel_id}]: <E< ({size}) [ {IntegraHelper.hex_str(pdu )} ]" )
            data = self._read_data_from_pdu( pdu )

            return data

        async def _async_read_plain( self, source: bytes | None ) -> bytes:

            in_message: bool = False
            sync_bytes: int = 0
            buffer: bytes = bytes()
            raw: bytes = bytes()
            read_index = 0

            while True:
                if source is None:
                    read_chunk = await self.channel._async_channel_read( 1 )
                    if len( read_chunk ) == 0:
                        if len( raw ) > 0 and raw[1:].decode(DEFAULT_CODE_PAGE).startswith("Busy"):
                            raise IntegraChannelError(self.channel_id, IntegraChannelErrorCode.REMOTE_BUSY )
                        raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.REMOTE_CLOSED )
                    raw += read_chunk
                    read_byte = read_chunk[ 0 ]
                else:
                    read_byte = source[ read_index ]
                    read_index += 1
                    if read_index > len( source ):
                        raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.REMOTE_CLOSED )
                self._channel._stats.update_rx_bytes()

                if read_byte == FRAME_SYNC:
                    if in_message:
                        # syncBytes == 0 means special sequence or end of message
                        # otherwise we discard all received bytes
                        if sync_bytes != 0:
                            _LOGGER.warning( f"Received frame sync bytes, discarding input: {IntegraHelper.hex_str( buffer )}" )
                            # clear gathered bytes, we wait for new message
                            in_message = False
                            buffer = bytes()
                            raw = bytes()
                    sync_bytes += 1
                else:
                    if in_message:
                        if sync_bytes == 0:
                            # in sync, we have next messaged byte
                            buffer += bytes( [ read_byte ] )
                        elif sync_bytes == 1:
                            if read_byte == FRAME_SYNC_ESC:
                                buffer += bytes( [ FRAME_SYNC ] )
                            elif read_byte == FRAME_SYNC_END:
                                break
                            else:
                                _LOGGER.warning(
                                    f"Received invalid byte {read_byte}, discarding input: {IntegraHelper.hex_str( buffer )}" )
                                in_message = False
                                buffer = bytes()
                                raw = bytes()
                        else:
                            _LOGGER.error( f"Sync bytes in message: {len( buffer )}" )
                    elif sync_bytes >= 2:
                        in_message = True
                        buffer += bytes( [ read_byte ] )
                    # otherwise we ignore all bytes until synced
                    sync_bytes = 0

            return buffer

        async def async_read( self ) -> IntegraResponse | None:
            decrypted = await self._async_read_encrypted() if self._cipher is not None else None
            buffer = await self._async_read_plain( decrypted )

            if IntegraHelper.debug_message( buffer[ 0 ], DEBUG_SHOW_RESPONSES_RAW ):
                _LOGGER.debug( f"async_channel_read[{self.channel_id}]: <<< {IntegraHelper.hex_str( buffer )}" )

            return IntegraResponse.from_bytes( buffer )

        async def async_write( self, data: bytes ) -> None:

            self._channel._stats.update_tx_bytes( len( data ) )
            if self._cipher is not None:
                size = len( data )
                data = self._write_data_with_pdu( data )
                data = size.to_bytes( 1, "big" ) + data
                self._channel._stats.update_tx_enc_bytes( len( data ) )
                if DEBUG_SHOW_REQUESTS_ENC:
                    _LOGGER.debug( f"async_write[{self.channel_id}]: >E> ({size}) [ {IntegraHelper.hex_str(data)} ]" )

            return await self.channel._async_channel_write( data )

    def __init__( self, eventloop: AbstractEventLoop, integration_key: str, on_event: IntegraChannelEventCallback = None ) -> None:

        self._eventloop = eventloop
        self._write_lock: Lock = Lock()
        self._cmd_exec_lock: Lock = Lock()
        self._ping_task: Task | None = None
        self._read_task: Task | None = None
        self._keepalive: float = DEFAULT_KEEP_ALIVE
        self._last_write = datetime.now()
        self._response_handlers: list[ Callable[ [ IntegraResponse | BaseException ], bool ] ] = [ ]
        self._handler: IntegraChannel.EncryptionHandler = IntegraChannel.EncryptionHandler( self, integration_key )
        self._on_event: IntegraChannelEventCallback = on_event
        self._stats: IntegraChannelStats = IntegraChannelStats()

    @property
    def connected( self ) -> bool:
        return False

    @property
    def channel_id( self ) -> str:
        return ""

    @property
    def stats( self ):
        return self._stats

    async def _async_channel_connect( self, timeout: float = DEFAULT_CONN_TIMEOUT ) -> bool:
        return False

    async def _async_channel_read( self, count: int ) -> bytes:
        return bytes( 0 )

    async def _async_channel_write( self, data: bytes ):
        pass

    async def _async_channel_close( self ):
        pass

    async def _async_post_data( self, data: bytes ) -> None:

        if not self.connected:
            raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.NOT_CONNECTED )

        try:
            async with self._write_lock:
                await self._handler.async_write( data )
                self._last_write = datetime.now()

        except OSError as err:
            await self._async_close( IntegraChannel.CloseSource.REQUEST )
            raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.WRITE_ERROR, err ) from None

    async def _async_post_request( self, request: IntegraRequest ) -> None:
        payload = request.get_payload()
        if IntegraHelper.debug_message( request.command, DEBUG_SHOW_REQUESTS ):
            _LOGGER.debug( f"_async_post_request[{self.channel_id}]: >>> {request}" )

        if IntegraHelper.debug_message( request.command, DEBUG_SHOW_REQUESTS_RAW ):
            _LOGGER.debug( f"_async_post_request[{self.channel_id}]: >>> {IntegraHelper.hex_str( payload )}" )

        await self._async_post_data( payload )

    async def _async_send_request(
            self, request: IntegraRequest, timeout: float = DEFAULT_RESP_TIMEOUT
    ) -> IntegraResponse:
        """ Send message to controller and await response """

        # prevent controller overloading and command loss - wait until finished (lock released)
        async with (self._cmd_exec_lock):

            result: IntegraResponse | None = None
            response_reader = self._eventloop.create_future()

            def on_response( response: IntegraResponse | BaseException ) -> bool:

                if not response_reader.done():

                    if isinstance( response, BaseException ):
                        response_reader.set_result( response )
                        return False

                    elif (request.command == response.command) or (request.result_allowed and response.command == IntegraCommand.READ_RESULT):
                        response.bind_request( request )
                        response_reader.set_result( response )
                        return True

                return False

            self._response_handlers.append( on_response )
            try:
                await self._async_post_request( request )

                while True:
                    try:
                        result = await asyncio.wait_for( response_reader, timeout )
                        break

                    except AsyncTimeoutError:
                        break

                    except AsyncCancelledError as err:
                        raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.READ_ERROR, err )
            finally:
                try:
                    self._response_handlers.remove( on_response )
                except ValueError:
                    pass

            if isinstance( result, BaseException ):
                raise result
            else:
                if result is None:
                    result = IntegraResponse.error( request.command, IntegraResponseErrorCode.NO_RESPONSE )
                    result.bind_request( request )

                elif request.result_allowed and result.command == IntegraCommand.READ_RESULT:
                    result = IntegraResponse.result( request.command, result.data[ 0 ] )
                    result.bind_request( request )
                    if IntegraHelper.debug_message( request.command, DEBUG_SHOW_RESPONSES ):
                        _LOGGER.debug( f"_async_send_request[{self.channel_id}]: <<< {result}" )

            return result

    async def _async_close( self, close_source: CloseSource ) -> None:

        if not self.connected:
            return

        _LOGGER.debug( f"_async_close[{self.channel_id}:{close_source.name}]: closing connection" )

        self._ping_task = await self._task_shutdown( IntegraChannel.CloseSource.PING_TASK, self._ping_task, close_source )
        self._read_task = await self._task_shutdown( IntegraChannel.CloseSource.READ_TASK, self._read_task, close_source )

        async with self._write_lock:
            if not self.connected:
                _LOGGER.debug( f"_async_close[{self.channel_id}:{close_source.name}]: connection already closed" )
                # socket could be released during awaiting on lock. if so just return
                return

            await self._async_channel_close()

        _LOGGER.debug( f"_async_close[{self.channel_id}:{close_source.name}]: connection closed" )

        should_reconnect = False if close_source == IntegraChannel.CloseSource.DISCONNECT else True
        await self._async_do_event( IntegraChannelEvent.DISCONNECTED, should_reconnect )

    def is_channel_ctx( self, src_task: asyncio.Task ) -> bool:
        return (self._read_task is not None and self._read_task == src_task) or (self._ping_task is not None and self._ping_task == src_task)

    async def _async_do_event( self, event: IntegraChannelEvent, data: Any = None ) -> None:
        """Notify of event by calling provided callback"""
        if event == IntegraChannelEvent.CONNECTED:
            self._stats.restart()

        if self._on_event is not None:
            await self._on_event( self, event, data )

    async def _async_read_task( self ) -> None:

        task_self = asyncio.current_task()
        task_err: BaseException | None = None

        try:
            _LOGGER.debug( f"_async_read_task[{self.channel_id}]: STARTED" )
            while True:
                response = await  self._handler.async_read()
                if response:
                    begin_ts = datetime.now()
                    response_handled: bool = False
                    for response_handler in self._response_handlers[ : ]:
                        response_handled = response_handler( response )
                        if response_handled:
                            break

                    if IntegraHelper.debug_message( response.command, DEBUG_SHOW_RESPONSES ):
                        _LOGGER.debug( f"_async_read_task[{self.channel_id}]: <<< [{"H" if response_handled else " "}{"B" if response.broadcast else " "}] {response}" )

                    if not response_handled or response.broadcast:
                        try:
                            await self._async_do_event( IntegraChannelEvent.NOTIFICATION, response )
                        except BaseException as err:
                            _LOGGER.error( f"_async_read_task[{self.channel_id}]: FAILURE - error while dispatching notification, {err}" )
                            print( traceback.format_exc() )

                    if IntegraHelper.debug_message( response.command, DEBUG_SHOW_RESPONSES ) and DEBUG_SHOW_RESPONSES_TIME:
                        _LOGGER.debug( f"_async_read_task[{self.channel_id}]:          Dispatch time = {(datetime.now() - begin_ts).total_seconds():.3f} seconds" )

        except AsyncCancelledError:
            # _LOGGER.debug( f"_async_read_task[{self.channel_id}]: CANCELLED" )
            pass

        except BaseException as err:
            # self._read_task = None
            task_err = err
            await self._async_close( IntegraChannel.CloseSource.READ_TASK )

        finally:
            if task_err is None:
                _LOGGER.debug( f"_async_read_task[{self.channel_id}]: FINISHED {'(Cancelled)' if task_self.cancelling() != 0 else ''}" )
            else:
                for response_handler in self._response_handlers[ : ]:
                    response_handler( task_err )
                _LOGGER.debug( f"_async_read_task[{self.channel_id}]: FINISHED ({task_err})" )

    async def _async_ping_task( self ) -> None:
        """Perform dummy data posting to connected controller"""
        task_self = asyncio.current_task()
        task_err: BaseException | None = None

        try:
            _LOGGER.debug( f"_async_ping_task[{self.channel_id}]: STARTED" )
            cmd_data = IntegraCmdReadElementData( IntegraZoneElement, 1 )
            while True:
                last_write = (datetime.now() - self._last_write).total_seconds()
                if last_write < self._keepalive:
                    period = self._keepalive - last_write
                    await asyncio.sleep( period )
                else:
                    self._last_write = datetime.now()
                    await self.async_send_command( IntegraCommand.ELEMENT_READ_NAME, cmd_data )

        except AsyncCancelledError:
            # _LOGGER.debug( f"_async_ping_task[{self.channel_id}]: CANCELLED" )
            pass

        except BaseException as err:
            # self._ping_task = None
            task_err = err
            await self._async_close( IntegraChannel.CloseSource.PING_TASK )

        finally:
            if task_err is None:
                _LOGGER.debug( f"_async_ping_task[{self.channel_id}]: FINISHED {'(Cancelled)' if task_self.cancelling() != 0 else ''}" )
            else:
                _LOGGER.error( f"_async_ping_task[{self.channel_id}]: FINISHED ({task_err})" )

    async def _task_shutdown(
            self, task_name: CloseSource, task: Task, close_source: CloseSource
    ) -> None:

        if task:
            if task_name != close_source:
                _LOGGER.debug( f"_task_shutdown[{self.channel_id}:{close_source.name}] requesting cancellation for task '{task_name.name}'" )
                task.cancel( close_source.name )

            try:
                if task != asyncio.current_task():
                    await task
            except AsyncCancelledError:
                _LOGGER.debug( f"_task_shutdown[{self.channel_id}:{close_source.name}]  task '{task_name.name}' canceled" )
                pass

        return None

    async def async_connect( self, timeout: float = 30.0 ) -> bool:

        if self.connected:
            _LOGGER.warning( f"async_connect[{self.channel_id}] Already connected" )
            return True

        try:
            if await self._async_channel_connect( timeout ):
                self._read_task = self._eventloop.create_task( self._async_read_task(), name=IntegraChannel.CloseSource.READ_TASK.value )
                self._ping_task = self._eventloop.create_task( self._async_ping_task(), name=IntegraChannel.CloseSource.PING_TASK.value )
                await self._async_do_event( IntegraChannelEvent.CONNECTED, None )
                return True

        except BaseException as err:
            _LOGGER.error( f"async_connect[{self.channel_id}] channel connect failed, {err}" )
            await self._async_close( IntegraChannel.CloseSource.CONNECT )
            raise

        return False

    async def async_disconnect( self, reconnect: bool = False ) -> None:
        await self._async_close(
            IntegraChannel.CloseSource.REQUEST if reconnect else IntegraChannel.CloseSource.DISCONNECT )

    async def async_post_command( self, command: IntegraCommand, data: IntegraCmdData | bytes | None = None ) -> None:
        await self._async_post_request( IntegraRequest( command, data ) )

    async def async_send_command(
            self, command: IntegraCommand, data: IntegraCmdData | bytes | None = None, timeout: float = DEFAULT_RESP_TIMEOUT
    ) -> IntegraResponse:

        request = IntegraRequest( command, data )
        response = await self._async_send_request( request, timeout )
        return response
