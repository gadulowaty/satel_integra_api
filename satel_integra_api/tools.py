from datetime import datetime
from enum import IntEnum

class IntegraHelper:

    @staticmethod
    def list_from_bytes( data: bytes, bit_length: int | None, one_base: bool = True ) -> list[ int ]:
        result = [ ]
        bit_length = bit_length if bit_length is not None else len( data ) * 8
        max_bytes = (bit_length / 8) if bit_length else len( bytes )
        list_item_base = 0
        cur_byte = 0
        for byte in data:
            if cur_byte >= max_bytes:
                break
            for list_item_bit in range( 0, 8 ):
                if byte & (1 << list_item_bit):
                    result.append( list_item_base + list_item_bit + (1 if one_base else 0) )
            list_item_base += 8
            cur_byte += 1
        return result

    @staticmethod
    def list_to_bytes( lst: list[ int ], bit_length: int = 128, one_base: bool = True ) -> bytes:
        result = bytearray( int( bit_length / 8 ) )
        if lst is not None:
            for lst_item in lst:
                lst_item -= (1 if one_base else 0)
                if lst_item < 0:
                    continue
                lst_item = lst_item % bit_length
                result_byte = int( lst_item / 8 )
                result_bit = (lst_item - (result_byte * 8))
                result[ result_byte ] |= (1 << result_bit)

        return bytes( result )

    @staticmethod
    def checksum( payload ) -> int:
        """Function to calculate checksum as per Satel manual."""
        crc = 0x147A
        for b in payload:
            # rotate (crc 1 bit left)
            crc = ((crc << 1) & 0xFFFF) | (crc & 0x8000) >> 15
            crc = crc ^ 0xFFFF
            crc = (crc + (crc >> 8) + b) & 0xFFFF
        return crc

    @staticmethod
    def decode_date_hex( date: bytes ) -> datetime:
        date_len = len( date )

        year = int( f"{date[ 0 ]:02X}{date[ 1 ]:02X}" ) if date_len > 1 else 0
        month = int( f"{date[ 2 ]:02X}" ) if date_len > 2 else 0
        day = int( f"{date[ 3 ]:02X}" ) if date_len > 3 else 0
        hours = int( f"{date[ 4 ]:02X}" ) if date_len > 4 else 0
        minutes = int( f"{date[ 5 ]:02X}" ) if date_len > 5 else 0
        seconds = int( f"{date[ 6 ]:02X}" ) if date_len > 6 else 0
        return datetime( year, month, day, hours, minutes, seconds ) if year > 0 and month > 0 and day > 0 else datetime.min

    @staticmethod
    def decode_date_str( date: bytes ) -> datetime:
        date_len = len( date )

        year = int( date[ 0:4 ].decode() ) if date_len > 3 else 0
        month = int( date[ 4:6 ].decode() ) if date_len > 5 else 0
        day = int( date[ 6:8 ].decode() ) if date_len > 7 else 0

        return datetime( year, month, day, 0, 0, 0 ) if year > 0 and month > 0 and day > 0 else datetime.min

    @staticmethod
    def decode_version( version: bytes ) -> (int, int, datetime):
        version_len = len( version )

        major = int( version[ 0:1 ].decode() ) if version_len > 0 else 0
        minor = int( version[ 1:3 ].decode() ) if version_len > 2 else 0
        date = IntegraHelper.decode_date_str( version[ 3:11 ] ) if version_len > 10 else datetime.min

        return major, minor, date

    @staticmethod
    def user_code_to_bytes( user_code: str, prefix_code: str ) -> bytes:
        code_str = prefix_code[ 0:8 ] if type( prefix_code ) is str else ""
        if type( user_code ) is str:
            code_str += user_code[ 0:8 ]
        result = bytes.fromhex( code_str.ljust( 16, 'F' ) )
        return result

    @staticmethod
    def code_to_bytes( code: str, max_len: int ):
        return bytes.fromhex( code[ 0:max_len ].ljust( max_len, 'F' ) )

    @staticmethod
    def parts_from_bytes( parts_data: bytes, bit_length: int | None = None ) -> list[ int ]:
        return IntegraHelper.list_from_bytes( parts_data, bit_length, True )

    @staticmethod
    def zones_from_bytes( zones_data: bytes, bit_length: int | None = None ) -> list[ int ]:
        return IntegraHelper.list_from_bytes( zones_data, bit_length, True )

    @staticmethod
    def outputs_from_bytes( outputs_data: bytes, bit_length: int | None = None ) -> list[ int ]:
        return IntegraHelper.list_from_bytes( outputs_data, bit_length, True )

    @staticmethod
    def output_from_byte( output_id: int ) -> int:
        return 256 if output_id == 0 else output_id

    @staticmethod
    def expanders_from_bytes( expanders_data: bytes, bit_length: int | None = None ) -> list[ int ]:
        return IntegraHelper.list_from_bytes( expanders_data, bit_length, True )

    @staticmethod
    def doors_from_bytes( door_data: bytes, bit_length: int | None = None ) -> list[ int ]:
        return IntegraHelper.list_from_bytes( door_data, bit_length, True )

    @staticmethod
    def locks_from_bytes( door_data: bytes, bit_length: int | None = None ) -> list[ int ]:
        return IntegraHelper.list_from_bytes( door_data, bit_length, True )

    @staticmethod
    def parts_to_bytes( parts: list[ int ] | None, bit_length: int = 32 ) -> bytes:
        return IntegraHelper.list_to_bytes( parts, bit_length, True )

    @staticmethod
    def zones_to_bytes( zones: list[ int ] | None, bit_length: int = 128 ) -> bytes:
        return IntegraHelper.list_to_bytes( zones, bit_length, True )

    @staticmethod
    def outputs_to_bytes( outputs: list[ int ] | None, bit_length: int = 128 ) -> bytes:
        return IntegraHelper.list_to_bytes( outputs, bit_length, True )

    @staticmethod
    def output_to_byte( output_no ) -> int:
        return (0 if output_no > 255 else output_no) & 0xFF

    @staticmethod
    def expanders_to_bytes( expanders: list[ int ] | None, bit_length: int = 64 ) -> bytes:
        return IntegraHelper.list_to_bytes( expanders, bit_length, True )

    @staticmethod
    def doors_to_bytes( doors: list[ int ] | None, bit_length: int = 64 ) -> bytes:
        return IntegraHelper.list_to_bytes( doors, bit_length, True )

    @staticmethod
    def locks_to_bytes( locks: list[ int ] | None, bit_length: int = 64 ) -> bytes:
        return IntegraHelper.list_to_bytes( locks, bit_length, True )

    @staticmethod
    def debug_message( cmd: int, msg_filter: list[ int ] | bool ) -> bool:
        if type( msg_filter ) is bool:
            return msg_filter
        return cmd in msg_filter

    @staticmethod
    def hex_str( data, fmt: str = "02X", prefix: str = "0x", separator: str = ", " ) -> str:
        hex_msg = ""
        for c in data:
            hex_msg += prefix + format( c, fmt ) + separator
        return hex_msg.rstrip( ', ' )

    @staticmethod
    def users_no_from_bytes( users_data: bytes, bit_length: int = None, is_admin: bool = False ) -> list[ int ]:
        result = IntegraHelper.list_from_bytes( users_data, bit_length, True )
        if is_admin:
            result = [ 0xF0 + user_no for user_no in result ]
        return result

    @staticmethod
    def admin_no_from_bytes( admins_data: bytes ) -> list[ int ]:
        return IntegraHelper.users_no_from_bytes( admins_data, 8, True )

    @staticmethod
    def btns_from_bytes( btns_data, bit_length: int ) -> list[ bool ]:
        max_range = min( len( btns_data ) * 8, bit_length )
        result: list[ bool ] = [ False ] * max_range
        for index in range( 0, max_range ):
            byte_index, bit_index = divmod(index, 8 )
            result[index] = True if btns_data[ byte_index ] & ( 1 << bit_index ) != 0 else False
        return result

    @staticmethod
    def str_to_enum( enum : type[IntEnum], str_value: str ) -> IntEnum:
        for item in enum:
            if str_value.upper() == item.name.upper():
                return item
        return enum(0)

