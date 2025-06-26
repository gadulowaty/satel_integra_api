import asyncio
import socket
import logging

from asyncio import StreamReader, StreamWriter, AbstractEventLoop

from .const import DEFAULT_CONN_TIMEOUT
from .channel import IntegraChannel, IntegraChannelEventCallback, IntegraChannelError, IntegraChannelErrorCode

_LOGGER = logging.getLogger( __name__ )


class IntegraChannelTCP( IntegraChannel ):

    def __init__( self, eventloop: AbstractEventLoop, host: str, port: int, integration_key: str, on_event: IntegraChannelEventCallback = None ) -> None:
        super().__init__( eventloop, integration_key, on_event )
        self._host: str = host
        self._port: int = port

        self._local_addr: str = ""
        self._local_port: int = -1
        self._remote_addr: str = ""
        self._remote_port: int = -1
        self._tcp_reader: StreamReader | None = None
        self._tcp_writer: StreamWriter | None = None
        self._socket: socket.socket | None = None

    async def _async_channel_connect( self, timeout: float = DEFAULT_CONN_TIMEOUT ) -> bool:

        self._socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self._socket.setblocking( False )
        self._socket.setsockopt( socket.IPPROTO_TCP, socket.TCP_NODELAY, 1 )

        _LOGGER.debug( f"Trying to connect to {self.host} at port {self.port}" )

        try:
            connect_oper = self._eventloop.sock_connect( self._socket, (self.host, self.port) )
            await asyncio.wait_for( connect_oper, timeout )

        except TimeoutError as err:
            await self._async_close( IntegraChannelTCP.CloseSource.CONNECT )
            raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.CONN_TIMEOUT, err )

        except OSError as err:
            await self._async_close( IntegraChannelTCP.CloseSource.CONNECT )
            raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.CONN_REFUSED, err )

        self._local_addr, self._local_port = self._socket.getsockname()
        self._remote_addr, self._remote_port = self._socket.getpeername()

        _LOGGER.debug( f"async_connect[{self.host}] connection established ({self._local_addr}:{self._local_port} <==> "
                       f"{self._remote_addr}:{self._remote_port})" )

        self._tcp_reader, self._tcp_writer = await asyncio.open_connection( sock=self._socket )
        return True

    async def _async_channel_close( self ):

        self._local_addr = ""
        self._local_port = -1
        self._remote_addr = ""
        self._remote_port = -1

        if self._tcp_writer:
            self._tcp_writer.close()
            self._tcp_writer = None

        self._tcp_reader = None

        self._socket.close()
        self._socket = None

    async def _async_channel_read( self, count: int ):
        try:
            return await self._tcp_reader.read( count )
        except Exception as err:
            raise IntegraChannelError( self.channel_id, IntegraChannelErrorCode.READ_ERROR, err ) from err

    async def _async_channel_write( self, data: bytes ):
        if self._tcp_writer is not None:
            self._tcp_writer.write( data )
            await self._tcp_writer.drain()

    @property
    def channel_id( self ) -> str:
        return f"{self.host}:{self.port}"

    @property
    def connected( self ) -> bool:
        return self._socket is not None

    @property
    def host( self ) -> str:
        return self._host

    @property
    def port( self ) -> int:
        return self._port
