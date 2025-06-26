from enum import IntEnum

from .const import FRAME_START, FRAME_END, FRAME_SYNC, FRAME_SYNC_ESC, FRAME_LEN_MIN
from .base import IntegraEntity, IntegraError
from .commands import IntegraCommand, IntegraCmdData
from .tools import IntegraHelper


class IntegraResponseErrorCode( IntEnum ):
    NO_ERROR = 0x00
    USER_CODE_NOT_FOUND = 0x01
    NO_ACCESS = 0x02
    USER_NOT_EXISTS = 0x03
    USER_ALREADY_EXISTS = 0x04
    WRONG_CODE_OR_CODE_ALREADY_EXISTS = 0x05
    TELEPHONE_CODE_ALREADY_EXISTS = 0x06
    CHANGED_CODE_IS_THE_SAME = 0x07
    OTHER_ERROR = 0x08
    CANNOT_ARM_USE_FORCE = 0x11
    CANNOT_ARM = 0x12
    OTHER_ERRORS_80 = 0x80
    OTHER_ERRORS_81 = 0x81
    OTHER_ERRORS_82 = 0x82
    OTHER_ERRORS_83 = 0x83
    OTHER_ERRORS_84 = 0x84
    OTHER_ERRORS_85 = 0x85
    OTHER_ERRORS_86 = 0x86
    OTHER_ERRORS_87 = 0x87
    OTHER_ERRORS_88 = 0x88
    OTHER_ERRORS_89 = 0x89
    OTHER_ERRORS_8A = 0x8A
    OTHER_ERRORS_8B = 0x8B
    OTHER_ERRORS_8C = 0x8C
    OTHER_ERRORS_8D = 0x8D
    OTHER_ERRORS_8E = 0x8E
    OTHER_ERRORS_8F = 0x8F
    COMMAND_ACCEPTED = 0xFF
    NO_RESPONSE = 0x100
    UNKNOWN_ERROR = 0x101


IntegraResponseErrorCodes = set( item.value for item in IntegraResponseErrorCode )


class IntegraMessage( IntegraEntity ):

    def __str__( self ):
        result = f"{self.__class__.__name__}[ Cmd=0x{self.command:02X}:{self.command.name}"
        data_type = type( self.data )
        if issubclass( data_type, IntegraCmdData ):
            result += f"; Data=[ {self.data} ]"
            payload = self.data.to_bytes()
            result += f"; Raw({len( payload )})=[ {IntegraHelper.hex_str( payload )} ])"
        elif isinstance( self.data, bytes ):
            result += f"; Data({len( self.data )})=[ {IntegraHelper.hex_str( self.data )} ]"
        elif isinstance( self.data, bytearray ):
            raise IntegraError( "Invalid data type in IntegraMessage.", self )

        return result + " ]"

    def __init__( self, command: IntegraCommand, data: IntegraCmdData | bytes | None = None ):
        super().__init__()
        self._command: IntegraCommand = command
        self._data: IntegraCmdData | bytes = data

    @property
    def command( self ) -> IntegraCommand:
        return self._command

    @property
    def data( self ) -> IntegraCmdData | bytes:
        return self._data


class IntegraRequest( IntegraMessage ):

    def __init__( self, command: IntegraCommand, data: IntegraCmdData | None = None ):
        super().__init__( command, data )
        self._broadcast: bool = False
        self._result_allowed = True

    @property
    def broadcast( self ) -> bool:
        return self._broadcast or ((self.command >= IntegraCommand.READ_ZONES_VIOLATION) and (self.command <= IntegraCommand.READ_TROUBLES_MEMORY_PART8))

    @property
    def result_allowed( self ) -> bool:
        return self._result_allowed

    def get_payload( self ) -> bytes:
        payload: bytes = bytes( [ self.command.value ] )

        data_type = type( self.data )
        if issubclass( data_type, IntegraCmdData ):
            payload += self.data.to_bytes()
        elif data_type is bytes:
            payload += self.data
            raise IntegraError( "Invalid data type (bytes) in IntegraRequest." )
        elif data_type is bytearray:
            raise IntegraError( "Invalid data type (bytearray) in IntegraRequest." )

        crc = IntegraHelper.checksum( payload )
        payload += bytes( [ (crc >> 8) & 0xff, crc & 0xff ] )
        payload = payload.replace( bytes( [ FRAME_SYNC ] ), bytes( [ FRAME_SYNC, FRAME_SYNC_ESC ] ) )
        return bytes( FRAME_START ) + payload + bytes( FRAME_END )


class IntegraRequestError( IntegraError ):

    def __init__( self, command: IntegraCommand | None, error_code: IntegraResponseErrorCode, error_code_no: int ):
        super().__init__()
        self._command: IntegraCommand | None = command
        self._error_code: IntegraResponseErrorCode = error_code
        self._error_code_no: int = error_code_no

    @property
    def command(self):
        return self._command

    @property
    def error_code(self) -> IntegraResponseErrorCode:
        return self._error_code

    @property
    def error_code_no(self) -> int:
        return self._error_code_no

    @property
    def message( self ) -> str:
        if self.command is not None:
            return f"Request {self.command.name} failed, error code was {self.error_code.name} ({self.error_code_no})"
        return f"Integra request failed, error code was {self.error_code.name} ({self.error_code_no})"


class IntegraResponse( IntegraMessage ):

    @classmethod
    def register_decoder( cls ):
        pass

    def __str__( self ):
        error_code_str = f"{self.error_code.name}"
        if self.error_code == IntegraResponseErrorCode.UNKNOWN_ERROR:
            error_code_str += f" (0x{self.error_code_no:02X})"
        else:
            error_code_str += f" (0x{self.error_code.value:02X})"

        if self.data is not None:
            return f"{self.__class__.__name__}[ Cmd={self.command.name} (0x{self.command:02X}); ErrorCode={error_code_str}; Data({len( self.data )})=[ {IntegraHelper.hex_str( self.data )} ] ]"
        return f"{self.__class__.__name__}[ Cmd={self.command.name} (0x{self.command:02X}); ErrorCode={error_code_str} ]"

    def __init__( self, command: IntegraCommand, data: bytes | None = None ):
        super().__init__( command, data if data is not None else bytes() )
        self._request: IntegraRequest | None = None
        self._error_code: IntegraResponseErrorCode = IntegraResponseErrorCode.NO_ERROR
        self._error_code_no: int = self._error_code.value

    def bind_request( self, request: IntegraRequest ) -> None:
        self._request = request

    @property
    def broadcast( self ) -> bool:
        return (self._request is not None and self._request.broadcast) or (self.command == IntegraCommand.READ_OUTPUT_POWER) or (self.command == IntegraCommand.READ_ZONE_TEMPERATURE) or (
                (self.command >= IntegraCommand.READ_ZONES_VIOLATION) and (self.command <= IntegraCommand.READ_TROUBLES_MEMORY_PART8))

    @property
    def request( self ) -> IntegraRequest | None:
        return self._request

    @property
    def error_code( self ) -> IntegraResponseErrorCode:
        return self._error_code

    @property
    def error_code_no( self ) -> int:
        return self._error_code_no

    @property
    def success( self ) -> bool:
        return self._error_code == IntegraResponseErrorCode.NO_ERROR or self._error_code == IntegraResponseErrorCode.COMMAND_ACCEPTED

    @staticmethod
    def from_bytes( payload: bytes ) -> 'IntegraResponse | None':
        if len( payload ) >= FRAME_LEN_MIN:
            command = IntegraCommand( payload[ 0 ] )
            data = payload[ 1:-2 ] if len( payload ) > FRAME_LEN_MIN else None
            crc = (payload[ -2 ] << 8) | payload[ -1 ]
            crc_check = IntegraHelper.checksum( payload[ 0:-2 ] )
            if crc == crc_check:
                return IntegraResponse( command, data )

        return None

    @staticmethod
    def result( command: IntegraCommand, error_code_no: int ):
        result = IntegraResponse( command )
        result._error_code_no = error_code_no
        result._error_code = IntegraResponseErrorCode( error_code_no ) if error_code_no in IntegraResponseErrorCodes else IntegraResponseErrorCode.UNKNOWN_ERROR
        return result

    @staticmethod
    def error( command: IntegraCommand, err_code: IntegraResponseErrorCode ):
        return IntegraResponse.result( command, err_code.value )
