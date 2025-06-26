from enum import IntEnum, Flag

from .const import DEFAULT_CODE_PAGE
from .data import IntegraEntityData, IntegraBuffer
from .tools import IntegraHelper


class IntegraUserKind( IntEnum ):
    INVALID = 0
    OTHER = 0
    USER = 1
    MASTER = 2
    SERVICE = 3

    @staticmethod
    def from_user_no( user_no: int ) -> 'IntegraUserKind':

        if user_no >= 255:
            return IntegraUserKind.SERVICE
        elif user_no >= 241:
            return IntegraUserKind.MASTER
        elif user_no >= 0:
            return IntegraUserKind.USER
        return IntegraUserKind.INVALID


class IntegraUserRights( Flag ):
    # BRAK
    NONE = 0x00000000
    # 1. Załączanie czuwania
    ARMING = 0x00000001
    # 2. Wyłączanie czuwania
    DISARMING = 0x00000002
    # 4. Kasowanie alarmu strefy
    ALARM_CLEAR_IN_PART = 0x00000004
    # 5. Kasowanie alarmu partycji
    ALARM_CLEAR_IN_OBJECT = 0x00000008
    # 6. Kasowanie alarmu innych partycji
    ALARM_CLEAR_ALL_SYSTEM = 0x00000010
    # 8. Odroczenie auto-uzbrojenia
    ARM_DEFERING = 0x00000020
    # 12. Zmiana hasł
    CODE_CHANGING = 0x00000040
    # 13. Edycja użytkowników
    USERS_EDITING = 0x00000080
    # 14. Blokowanie wejść
    ZONES_BYPASSING = 0x00000100
    # 16. Programowanie czasu
    CLOCK_SETTING = 0x00000200
    # 17. Sprawdzanie aktualnych awarii
    TROUBLES_VIEWING = 0x00000400
    # 18. Przeglądanie zdarzeń
    EVENTS_VIEWING = 0x00000800
    # 19. Resetowanie czujek
    ZONES_RESETING = 0x00001000
    # 20. Zmiana opcji
    OPTIONS_CHANGING = 0x00002000
    # 21. Dostęp do testów
    TESTS = 0x00004000
    # 22. Uruchomienie funkcji download
    DOWNLOADING = 0x00008000
    # 3. Wyłącza, gdy kto inny załączył
    CAN_ALWAYS_DISARM = 0x00010000
    # 7. Kasowanie powiadamiania telefonicznego
    VOICE_MESSAGE_CLEARING = 0x00020000
    # 24. Podgląd stanu systemu w programie GUARDX
    GUARDX_USING = 0x00040000
    # 11. Dostęp do stref zablokowanych czasowo
    ACCESS_TEMP_BLOCK_PARTS = 0x00080000
    # 9. Hasło pierwsze dla strefy na dwa hasła
    ENTERING_1ST_CODE = 0x00100000
    # 10. Hasło drugie dla strefy na dwa hasła
    ENTERING_2ND_CODE = 0x00200000
    # 23. Sterowanie wyjściami BI, MONO, TEL
    OUTPUTS_CONTROL = 0x00400000
    # 25. Wyłączanie zatrzaśniętych wyjść
    CLEARING_LATCHED_OUTPUTS = 0x00800000
    # 15. Trwałe blokowanie wejść
    ZONES_ISOLATING = 0x01000000
    # 26. Użytkownik prosty
    SIMPLE_USER = 0x02000000
    # 27. Administrator
    MASTER_USER = 0x04000000


class IntegraUserType( IntEnum ):
    NORMAL = 0
    SINGLE = 1
    TIME_RENEWABLE = 2
    TIME_NOT_RENEWABLE = 3
    DURESS = 4
    MONO_OUTPUTS = 5
    BI_OUTPUTS = 6
    PARTS_TEMP_BLOCKING = 7
    ACCESS_TO_CASH_MACHINE = 8
    GUARD = 9
    SCHEDULE = 10
    INVALID = 15


IntegraUserTypes = [ item.value for item in IntegraUserType ]


class IntegraUserCodesOpts( Flag ):
    NONE = 0x00
    CODE_NOT_CHAGED_YET = 0x01
    USER_CODE_COLLISION = 0x02
    PHONE_CODE_CHANGED = 0x04
    PREFIX_NEED_CHANGE = 0x08
    PHONE_CODE_NEED_CHANGE = 0x10
    USER_CODE_NEED_CHANGE = 0x20


class IntegraUserDeviceMgmtFunc( IntEnum ):
    UNKNOWN = ord( " " )
    RESULT = ord( "?" )
    READ_LIST = ord( "0" )
    READ_PROXIMITY_CARD = ord( "1" )
    WRITE_PROXIMITY_CARD = ord( "2" )
    READ_DALLAS_DEV = ord( "3" )
    WRITE_DALLAS_DEV = ord( "4" )
    READ_INTRX_KEY_FOB = ord( "7" )
    WRITE_INTRX_KEY_FOB = ord( "8" )
    READ_ABAX_KEY_FOB = ord( "9" )
    WRITE_ABAX_KEY_FOB = ord( "A" )


IntegraUserDeviceMgmtFuncs = [ item.value for item in IntegraUserDeviceMgmtFunc ]


class IntegraUserData( IntegraEntityData ):

    def __init__( self, offset=0 ):
        super().__init__()
        self._offset = offset
        self._user_no = -1
        self._kind: IntegraUserKind = IntegraUserKind.INVALID

    @property
    def user_no( self ):
        return self._user_no

    @user_no.setter
    def user_no( self, user_no: int ):
        self._user_no = user_no & 0xFF
        self._kind = IntegraUserKind.from_user_no( self._user_no )

    @property
    def kind( self ) -> IntegraUserKind:
        return self._kind

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserNo": f"{self.user_no}",
            "Kind": f"{self._kind.name}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self.user_no = payload[ self._offset ] if payload_len > self._offset else -1

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_byte( self.user_no )


class IntegraUserDevice( IntegraUserData ):

    def __init__( self ) -> None:
        super().__init__( 1 )


class IntegraUserCard( IntegraUserDevice ):

    def __init__( self, serial_len: int ) -> None:
        super().__init__()
        self._serial_len = serial_len
        self._serial_no: str = "".rjust( self._serial_len * 2, "0" )

    @property
    def serial_len( self ):
        return self._serial_len

    @property
    def serial_no( self ):
        return self._serial_no.rjust( self._serial_len * 2, "0" )

    @serial_no.setter
    def serial_no( self, serial_no: str ):
        self._serial_no = serial_no[ 0:self._serial_len * 2 ].rjust( self._serial_len * 2, "0" ).upper()

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "SerialNo": f"{self._serial_no}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self.serial_no = payload[ 2:2 + self.serial_len ].hex() if payload_len > 1 + self.serial_len else ""

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_bytes( bytes.fromhex( self.serial_no ) )


class IntegraUserProximityCard( IntegraUserCard ):

    def __init__( self ) -> None:
        super().__init__( 5 )


class IntegraUserDallasDev( IntegraUserCard ):

    def __init__( self ) -> None:
        super().__init__( 6 )


class IntegraUserKeyFob( IntegraUserDevice ):

    def __init__( self, btns_count: int, serial_mask: int ) -> None:
        super().__init__()
        self._btns_count = btns_count
        self._serial_no: int = 0
        self._serial_mask: int = serial_mask
        self._zones: list[ int ] = [ 0 ] * btns_count
        self._no_events: list[ bool ] = [ False ] * btns_count

    @property
    def btns_count( self ):
        return self._btns_count

    @property
    def serial_no( self ) -> int:
        return self._serial_no & self._serial_mask

    @serial_no.setter
    def serial_no( self, serial_no: int ):
        self._serial_no = serial_no & self._serial_mask

    @property
    def no_events( self ) -> list[ bool ]:
        return self._no_events

    @no_events.setter
    def no_events( self, no_events: list[ bool ] ):
        index = 0
        for value in no_events:
            self._no_events[ index ] = value
            index += 1
            if index >= self._btns_count:
                break

    @property
    def zones( self ) -> list[ int ]:
        return self._zones

    @zones.setter
    def zones( self, zones: list[ int ] ):
        index = 0
        for value in zones:
            self._zones[ index ] = value
            index += 1
            if index >= self._btns_count:
                break

    def _no_events_get( self ) -> int:
        result = 0
        index = 0
        for value in self.no_events:
            if value:
                result |= 1 << index
            index += 1
        return result

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "SerialNo": f"{self._serial_no}",
            "Zones": f"{self.zones}",
            "NoEvents": f"{self.no_events}",
        } )


class IntegraUserIntRxKeyFob( IntegraUserKeyFob ):

    def __init__( self ) -> None:
        super().__init__( 6, 0x0FFFFFFF )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self.serial_no = int.from_bytes( payload[ 2:6 ], "big" )
        self.zones = list( payload[ 6:6 + self._btns_count ] )
        self.no_events = IntegraHelper.btns_from_bytes( payload[ 6 + self._btns_count:6 + self._btns_count + 1 ], self._btns_count )

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_bytes( self.serial_no.to_bytes( 4, "big" ) )
        payload.put_bytes( bytes( self.zones ) )
        payload.put_byte( self._no_events_get() )


class IntegraUserAbaxKeyFob( IntegraUserKeyFob ):

    def __init__( self ) -> None:
        super().__init__( 6, 0x000FFFFF )
        self._ack_outputs: list[ int ] = [ 0, 0, 0 ]

    @property
    def ack_outputs( self ) -> list[ int ]:
        return self._ack_outputs

    @ack_outputs.setter
    def ack_outputs( self, outputs: list[ int ] ):
        index = 0
        for value in outputs:
            self._ack_outputs[ index ] = value if 0 <= value <= 8 else 0
            index += 1
            if index >= len( self._ack_outputs ):
                break

    @staticmethod
    def _ack_outputs_read( value: int ) -> list[ int ]:
        result = [ 0, 0, 0 ]
        index_result = 0
        for index in range( 0, 8 ):
            if value & (1 << index) != 0:
                result[ index_result ] = (index + 1)
                index_result += 1
                if index_result >= len( result ):
                    break
        return result

    def _ack_outputs_write( self ):
        result = 0
        index = 0
        for value in self._ack_outputs:
            if 0 < value <= 8:
                value -= 1
            result |= 1 << value
            index += 1
        return result

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "AckOutputs": f"{self.ack_outputs}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self.serial_no = int.from_bytes( payload[ 2:5 ], "big" )
        self.zones = list( payload[ 5:5 + self._btns_count ] )
        self.no_events = IntegraHelper.btns_from_bytes( payload[ 5 + self._btns_count:5 + self._btns_count + 1 ], self._btns_count )
        self.ack_outputs = self._ack_outputs_read( payload[ 5 + self._btns_count + 1 ] )

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_bytes( self.serial_no.to_bytes( 3, "big" ) )
        payload.put_bytes( bytes( self.zones ) )
        payload.put_byte( self._no_events_get() )
        payload.put_byte( self._ack_outputs_write() )


class IntegraUserLocks( IntegraUserData ):

    def __init__( self ) -> None:
        super().__init__()
        self._locks: list[ int ] = [ ]

    @property
    def locks( self ) -> list[ int ]:
        return self._locks

    @locks.setter
    def locks( self, locks: list[ int ] ) -> None:
        self._locks = locks

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Locks": f"{self._locks}",
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._locks = IntegraHelper.doors_from_bytes( payload[ 1: 9 ] ) if payload_len > 8 else [ ]

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.locks_to_bytes( self.locks ) )


class IntegraUsersList( IntegraUserData ):

    def __init__( self ) -> None:
        super().__init__()
        self._users_all: list[ int ] = [ ]
        self._users_edit: list[ int ] = [ ]

    @property
    def users_all( self ) -> list[ int ]:
        return self._users_all

    @property
    def users_edit( self ) -> list[ int ]:
        return self._users_edit

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UsersAll": f"{self._users_all}",
            "UsersEdit": f"{self._users_edit}"
        } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._users_all = IntegraHelper.users_no_from_bytes( payload[ 1: 31 ] ) if payload_len > 30 else [ ]
        self._users_edit = IntegraHelper.users_no_from_bytes( payload[ 31: 61 ] ) if payload_len > 60 else [ ]


class IntegraUserBase( IntegraUserData ):

    def __init__( self ) -> None:
        super().__init__()
        self._name: str = ""
        self._parts: list[ int ] = [ ]
        self._rights: IntegraUserRights = IntegraUserRights.NONE
        self._utype: IntegraUserType = IntegraUserType.INVALID
        self._time: int = 0
        self._time_temp: int = 0
        self._object_no: int = -1
        self._codes_opts: IntegraUserCodesOpts = IntegraUserCodesOpts.NONE

    @property
    def name( self ) -> str:
        return self._name

    @name.setter
    def name( self, name: str ):
        self._name = name[ 0:16 ]

    @property
    def parts( self ) -> list[ int ]:
        return self._parts

    @parts.setter
    def parts( self, parts: list[ int ] ):
        self._parts = parts

    @property
    def rights( self ) -> IntegraUserRights:
        return self._rights

    @rights.setter
    def rights( self, rights: IntegraUserRights ):
        self._rights = rights

    @property
    def time( self ) -> int:
        return self._time

    @time.setter
    def time( self, time: int ):
        self._time = time & 0xFF

    @property
    def utype( self ) -> IntegraUserType:
        return self._utype

    @utype.setter
    def utype( self, utype: IntegraUserType ):
        self._utype = utype
        if not self._utype in [ IntegraUserType.TIME_RENEWABLE, IntegraUserType.TIME_NOT_RENEWABLE, IntegraUserType.PARTS_TEMP_BLOCKING,
                                IntegraUserType.SCHEDULE ]:
            self._time = 0
            self._time_temp = 0

    @property
    def codes_opts( self ) -> IntegraUserCodesOpts:
        return self._codes_opts

    @property
    def object_no( self ) -> int | None:
        return self._object_no

    @object_no.setter
    def object_no( self, object_no: int ):
        self._object_no = object_no & 0x07

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "Name": f"'{self.name}'",
            "Parts": f"{self.parts}",
            "UType": f"{self.utype}",
            "Rights": f"{self.rights}",
            "ObjectNo": f"{self.object_no}",
        } )


class IntegraUserSelf( IntegraUserBase ):

    def __init__( self ) -> None:
        super().__init__()
        self._phone_code: str = ""
        self._existing_masters: list[ int ] = [ ]

    @property
    def phone_code( self ) -> str:
        return self._phone_code

    @property
    def existing_masters( self ) -> list[ int ]:
        return self._existing_masters

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        if self.kind == IntegraUserKind.SERVICE:
            fields.update( { "ExistingMasters": f"{self._existing_masters}" } )
        elif self.kind == IntegraUserKind.USER:
            fields.update( { "PhoneCode": f"'{self.phone_code}'" } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        if payload_len > 2:
            if self.kind == IntegraUserKind.USER:
                self._phone_code = payload[ 1:3 ].hex()
            elif self.kind == IntegraUserKind.SERVICE:
                self._existing_masters = IntegraHelper.admin_no_from_bytes( payload[ 1:2 ] )
        self._parts = IntegraHelper.parts_from_bytes( payload[ 3:7 ] ) if payload_len > 6 else [ ]
        if payload_len > 7:
            self._utype = IntegraUserType( payload[ 7 ] & 0x0F ) if (payload[ 7 ] & 0x0F) in IntegraUserTypes else IntegraUserType.INVALID
            self._rights = IntegraUserRights.ZONES_ISOLATING if (payload[ 7 ] & 0x20) else IntegraUserRights.NONE
            self._codes_opts |= IntegraUserCodesOpts.CODE_NOT_CHAGED_YET if (payload[ 7 ] & 0x80) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.USER_CODE_COLLISION if (payload[ 7 ] & 0x40) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.PHONE_CODE_CHANGED if (payload[ 7 ] & 0x10) else IntegraUserCodesOpts.NONE

        self._user_time = payload[ 8 ] if payload_len > 8 else 0
        self._rights |= IntegraUserRights( int.from_bytes( payload[ 9:12 ], "little" ) ) if payload_len > 11 else IntegraUserRights.NONE
        self._name = payload[ 12:28 ].decode( DEFAULT_CODE_PAGE ).strip( " " ) if payload_len > 27 else ""
        if payload_len > 28:
            self._rights |= IntegraUserRights.SIMPLE_USER if payload[ 28 ] & 0x80 else IntegraUserRights.NONE
            self._rights |= IntegraUserRights.MASTER_USER if payload[ 28 ] & 0x40 else IntegraUserRights.NONE
            self._codes_opts |= IntegraUserCodesOpts.PREFIX_NEED_CHANGE if (payload[ 28 ] & 0x20) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.PHONE_CODE_NEED_CHANGE if (payload[ 28 ] & 0x10) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.USER_CODE_NEED_CHANGE if (payload[ 28 ] & 0x08) else IntegraUserCodesOpts.NONE
            self._object_no = payload[ 28 ] & 0x07


class IntegraUser( IntegraUserBase ):

    def __init__( self ):
        super().__init__()
        self._user_no: int = 255
        self._user_code: str = ""
        self._phone_code: str = ""
        self._time_temp: int = 0
        self._utype: IntegraUserType = IntegraUserType.NORMAL
        self._object_no: int = 0

    @property
    def user_code( self ) -> str:
        return self._user_code

    @user_code.setter
    def user_code( self, user_code: str ):
        self._user_code = user_code[ 0:8 ]

    @property
    def phone_code( self ) -> str:
        return self._phone_code

    @phone_code.setter
    def phone_code( self, phone_code: str ):
        self._phone_code = phone_code[ 0:4 ]

    @property
    def schedule_no( self ) -> int:
        return self._time if self.utype == IntegraUserType.SCHEDULE else 0

    @schedule_no.setter
    def schedule_no( self, schedule_no: int ):
        if self.utype == IntegraUserType.SCHEDULE:
            if schedule_no < 1:
                self._time = 1
            elif schedule_no > 8:
                self._time = 8
            else:
                self._time = schedule_no

    @property
    def exists_durration( self ) -> int:
        return self._time if self.utype in [ IntegraUserType.TIME_RENEWABLE, IntegraUserType.TIME_NOT_RENEWABLE ] else 0

    @exists_durration.setter
    def exists_durration( self, exists_durration: int ):
        if self.utype in [ IntegraUserType.TIME_RENEWABLE, IntegraUserType.TIME_NOT_RENEWABLE ]:
            self._time = exists_durration & 0xFF
            self._time_temp = 0

    @property
    def schedule_durration( self ) -> int:
        return self._time_temp if self.utype == IntegraUserType.SCHEDULE else 0

    @schedule_durration.setter
    def schedule_durration( self, schedule_durration: int ):
        if self.utype == IntegraUserType.SCHEDULE:
            self._time_temp = schedule_durration & 0xFF

    @property
    def blocking_time( self ) -> int:
        return self._time if self.utype == IntegraUserType.PARTS_TEMP_BLOCKING else 0

    @blocking_time.setter
    def blocking_time( self, blocking_time: int ):
        if self.utype == IntegraUserType.PARTS_TEMP_BLOCKING:
            if blocking_time < 1:
                self._time = 1
            elif blocking_time > 109:
                self._time = 109
            else:
                self._time = blocking_time
            self._time_temp = 0

    @property
    def time_temp( self ) -> int:
        return self._time_temp

    @time_temp.setter
    def time_temp( self, time_temp: int ):
        self._time_temp = time_temp & 0xFF

    @staticmethod
    def from_other( other_user: 'IntegraUserOther' ) -> 'IntegraUser':
        return other_user.to_user()

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        fields.update( {
            "UserCode": f"'{self.user_code}'",
            "PhoneCode": f"'{self.phone_code}'",
        } )
        if self.utype == IntegraUserType.SCHEDULE:
            fields.update( {
                "ScheduleNo": f"{self.schedule_no}",
                "ScheduleDurration": f"{self.schedule_durration} day(s)",
            } )
        elif self.utype == IntegraUserType.PARTS_TEMP_BLOCKING:
            fields.update( {
                "BlockingTime": f"{self.blocking_time} min(s)",
            } )
        elif self.utype == IntegraUserType.TIME_NOT_RENEWABLE or self.utype == IntegraUserType.TIME_RENEWABLE:
            fields.update( {
                "ExistsDurration": f"{self.exists_durration} day(s)",
            } )

    def _write_bytes( self, payload: IntegraBuffer ):
        super()._write_bytes( payload )
        payload.put_bytes( IntegraHelper.code_to_bytes( self.user_code, 8 ) )
        payload.put_bytes( IntegraHelper.code_to_bytes( self.phone_code, 4 ) )
        payload.put_bytes( IntegraHelper.parts_to_bytes( self.parts ) )

        value = 0
        value |= ((1 if self.rights & IntegraUserRights.SIMPLE_USER == IntegraUserRights.SIMPLE_USER else 0) << 7)
        value |= ((1 if self.rights & IntegraUserRights.MASTER_USER == IntegraUserRights.MASTER_USER else 0) << 6)
        value |= ((1 if self.rights & IntegraUserRights.ZONES_ISOLATING == IntegraUserRights.ZONES_ISOLATING else 0) << 5)
        value |= (self.utype.value & 0x0F)
        payload.put_byte( value )

        if self.utype in [ IntegraUserType.TIME_RENEWABLE, IntegraUserType.TIME_NOT_RENEWABLE, IntegraUserType.PARTS_TEMP_BLOCKING, IntegraUserType.SCHEDULE ]:
            payload.put_byte( self.time )
        else:
            payload.put_byte( 0 )

        if self.utype in [ IntegraUserType.SCHEDULE ]:
            payload.put_byte( self.time_temp )
        else:
            payload.put_byte( 0 )

        payload.put_bytes( (self.rights.value & 0x00FFFFFF).to_bytes( 3, "little" ) )
        payload.put_bytes( self.name.ljust( 16, " " ).encode( DEFAULT_CODE_PAGE ) )


class IntegraUserOther( IntegraUserBase ):

    def __init__( self ) -> None:
        super().__init__()
        self._time_temp: int = 0

    @property
    def exists_durration( self ) -> int:
        return self._time if self.utype in [ IntegraUserType.TIME_RENEWABLE, IntegraUserType.TIME_NOT_RENEWABLE ] else 0

    @property
    def schedule_no( self ) -> int:
        return self._time if self.utype == IntegraUserType.SCHEDULE else 0

    @property
    def schedule_durration( self ) -> int:
        return self._time_temp if self.utype == IntegraUserType.SCHEDULE else 0

    @property
    def blocking_time( self ) -> int:
        return self._time if self.utype == IntegraUserType.PARTS_TEMP_BLOCKING else 0

    @property
    def time_temp( self ) -> int:
        return self._time_temp

    def _write_fields( self, fields: dict[ str, str ] ) -> None:
        super()._write_fields( fields )
        if self.utype == IntegraUserType.SCHEDULE:
            fields.update( {
                "ScheduleNo": f"{self.schedule_no}",
                "ScheduleDurration": f"{self.schedule_durration} day(s)",
            } )
        elif self.utype == IntegraUserType.PARTS_TEMP_BLOCKING:
            fields.update( {
                "BlockingTime": f"{self.blocking_time} min(s)",
            } )
        elif self.utype == IntegraUserType.TIME_NOT_RENEWABLE or self.utype == IntegraUserType.TIME_RENEWABLE:
            fields.update( {
                "ExistsDurration": f"{self.exists_durration} day(s)",
            } )

    def _read_bytes( self, payload: bytes, payload_len: int ) -> None:
        super()._read_bytes( payload, payload_len )
        self._parts = IntegraHelper.parts_from_bytes( payload[ 1:5 ] ) if payload_len > 4 else [ ]
        if payload_len > 5:
            self._utype = IntegraUserType( payload[ 5 ] & 0x0F ) if (payload[ 5 ] & 0x0F) in IntegraUserTypes else IntegraUserType.INVALID
            self._rights = IntegraUserRights.ZONES_ISOLATING if (payload[ 5 ] & 0x20) else IntegraUserRights.NONE
            self._codes_opts |= IntegraUserCodesOpts.CODE_NOT_CHAGED_YET if (payload[ 5 ] & 0x80) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.USER_CODE_COLLISION if (payload[ 5 ] & 0x40) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.PHONE_CODE_CHANGED if (payload[ 5 ] & 0x10) else IntegraUserCodesOpts.NONE
        self._time = payload[ 6 ] if payload_len > 6 else 0
        self._time_temp = payload[ 7 ] if payload_len > 7 else 0
        self._rights |= IntegraUserRights( int.from_bytes( payload[ 8:11 ], "little" ) ) if payload_len > 10 else IntegraUserRights.NONE
        self._name = payload[ 11:27 ].decode( DEFAULT_CODE_PAGE ).strip( " " ) if payload_len > 27 else ""
        if payload_len > 27:
            self._rights |= IntegraUserRights.SIMPLE_USER if payload[ 27 ] & 0x80 else IntegraUserRights.NONE
            self._rights |= IntegraUserRights.MASTER_USER if payload[ 27 ] & 0x40 else IntegraUserRights.NONE
            self._codes_opts |= IntegraUserCodesOpts.PREFIX_NEED_CHANGE if (payload[ 27 ] & 0x20) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.PHONE_CODE_NEED_CHANGE if (payload[ 27 ] & 0x10) else IntegraUserCodesOpts.NONE
            self._codes_opts |= IntegraUserCodesOpts.USER_CODE_NEED_CHANGE if (payload[ 27 ] & 0x08) else IntegraUserCodesOpts.NONE

            self._object_no = payload[ 27 ] & 0x07

    def to_user( self ) -> IntegraUser:
        result = IntegraUser()
        result.user_no = self.user_no
        result.name = self.name
        result.parts = self.parts
        result.utype = self.utype
        result.rights = self.rights
        result.time = self.time
        result.time_temp = self.time_temp
        return result
