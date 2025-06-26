from asyncio import AbstractEventLoop

from .channel import IntegraChannel, IntegraChannelEventCallback


class IntegraChannelRS232( IntegraChannel ):

    def __init__( self, eventloop: AbstractEventLoop, serial: str, speed: int, on_event: IntegraChannelEventCallback = None ) -> None:
        super().__init__( eventloop, "", on_event )
        self._serial: str = serial
        self._speed: int = speed

    @property
    def channel_id( self ) -> str:
        return f"{self.serial}"

    @property
    def serial( self ) -> str:
        return self._serial