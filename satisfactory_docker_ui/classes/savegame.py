import struct


class SaveGameHeader(object):
    def __init__(self, save_bytes: bytes = None, save_file: str = None):
        """
        Class to extract the header of a Satisfactory save game.

        It takes either a bytes object or the path to the file.

        :param save_bytes: The bytes-like object of the save game.
        :type save_bytes: bytearray
        :param save_file: The path to the file.
        :type save_file: str
        """
        self.save_bytes: bytes = save_bytes
        self.save_file: str = save_file

        self.valid_data: bool = True
        self.error_message_data: list = []

        if not (self.save_bytes or self.save_file):
            self.valid_data = False
            self.error_message_data.append("neither save_bytes nor save_file given")

        if self.save_bytes and self.save_file:
            self.valid_data = False
            self.error_message_data.append("save_bytes and save_file given - only one is allowed")

        if self.save_file:
            self._load_file()

        self.header_version: int = self._get_integer()
        self.save_version: int = self._get_integer()
        self.build_version: int = self._get_integer()
        self.world_type: str = self._get_string()
        self.world_properties: str = self._get_string()
        self.session_name: str = self._get_string()
        self.play_time: int = self._get_integer()
        self.save_date: int = self._get_integer(size=8, struct_format="q")
        self.session_visibility: bool = self._get_byte() if self.header_version >= 5 else None
        self.editor_object_version: int = self._get_integer() if self.header_version >= 7 else None
        self.mod_metadata: str = self._get_string() if self.header_version >= 8 else None
        self.mod_flags: int = self._get_integer() if self.header_version >= 8 else None

    def _load_file(self):
        with open(self.save_file, "rb") as save_file_stream:
            self.save_bytes = save_file_stream.read()

    def _get_integer(self, size=4, struct_order="<", struct_format="i"):
        _raw = self.save_bytes[:size]
        _temp_value = struct.unpack(f"{struct_order}{struct_format}", _raw)
        self.save_bytes = self.save_bytes[size:]

        return _temp_value[0]

    def _get_string(self, struct_order="<", struct_format="s"):
        _temp_value = ""
        _string_length = struct.unpack("<i", self.save_bytes[:4])[0]

        if _string_length:
            _raw = self.save_bytes[4:4 + _string_length - 1]
            _temp_value = struct.unpack(
                f"{struct_order}{_string_length-1}{struct_format}",
                _raw
            )
            _temp_value = _temp_value[0]
            _temp_value = _temp_value.decode()

        self.save_bytes = self.save_bytes[4 + _string_length:]

        return _temp_value

    def _get_byte(self, size=1, struct_order="<", struct_format="?"):
        _raw = self.save_bytes[:size]
        _temp_value = struct.unpack(f"{struct_order}{struct_format}", _raw)
        self.save_bytes = self.save_bytes[size:]

        return _temp_value[0]
