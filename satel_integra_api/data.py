from typing import Any

from .base import IntegraEntity


class IntegraBuffer:

    def __init__( self ) -> None:
        self._bytes = bytes()

    def get_bytes( self ):
        return self._bytes

    def put_byte( self, *data ):
        self._bytes += bytes( [ byte & 0xFF for byte in data ] )

    def put_bytes( self, data: bytes ):
        self._bytes += data


class IntegraEntityData( IntegraEntity ):

    def __init__( self ):
        super().__init__()

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        pass

    def _write_bytes( self, payload: IntegraBuffer ):
        pass

    def _read_json( self, json_data: dict[ str, Any ] ) -> None:
        pass

    def _write_json( self, json_data: dict[ str, Any ] ) -> None:
        pass

    def to_json( self ) -> dict:
        json_data = { }
        self._write_json( json_data )
        return json_data

    def to_bytes( self ) -> bytes:
        result = IntegraBuffer()
        self._write_bytes( result )
        return result.get_bytes()

    @classmethod
    def from_json( cls, json_data: dict[ str, Any ] ):
        result = cls()
        result._read_json( json_data )
        return result

    @classmethod
    def from_bytes( cls, payload: bytes ) -> 'IntegraEntityData':
        result = cls()
        result._read_bytes( payload, len( payload ) )
        return result

