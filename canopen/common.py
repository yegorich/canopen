import logging


logger = logging.getLogger(__name__)


class Variable(object):

    def __init__(self, od):
        self.od = od
        self._bits = Bits(self)

    def get_data(self):
        raise NotImplementedError("Variable is not readable")

    def set_data(self, data):
        raise NotImplementedError("Variable is not writable")

    @property
    def data(self):
        """Byte representation of the object (:class:`bytes`)."""
        if self.od.access_type == "wo":
            logger.warning("Variable is write only")
        return self.get_data()

    @data.setter
    def data(self, data):
        if "w" not in self.od.access_type:
            logger.warning("Variable is read only")
        self.set_data(data)

    @property
    def raw(self):
        """Raw representation of the object.

        This table lists the translations between object dictionary data types
        and Python native data types.

        +---------------------------+----------------------------+
        | Data type                 | Python type                |
        +===========================+============================+
        | UNSIGNEDxx                | :class:`int`               |
        +---------------------------+                            |
        | INTEGERxx                 |                            |
        +---------------------------+----------------------------+
        | BOOLEAN                   | :class:`bool`              |
        +---------------------------+----------------------------+
        | REALxx                    | :class:`float`             |
        +---------------------------+----------------------------+
        | VISIBLE_STRING            | :class:`str`               |
        |                           +----------------------------+
        |                           | ``unicode`` (Python 2)     |
        +---------------------------+----------------------------+
        """
        value = self.od.decode_raw(self.data)
        text = "Value of %s (0x%X:%d) is %s" % (
            self.od.name, self.od.index,
            self.od.subindex, value)
        if value in self.od.value_descriptions:
            text += " (%s)" % self.od.value_descriptions[value]
        logger.debug(text)
        return value

    @raw.setter
    def raw(self, value):
        logger.debug("Writing %s (0x%X:%d) = %s",
                     self.od.name, self.od.index,
                     self.od.subindex, value)
        self.data = self.od.encode_raw(value)

    @property
    def phys(self):
        """Physical value scaled with some factor (defaults to 1).

        On object dictionaries that support specifying a factor, this can be
        either a :class:`float` or an :class:`int`.
        Strings will be passed as is.
        """
        value = self.od.decode_phys(self.raw)
        if self.od.unit:
            logger.debug("Physical value is %s %s", value, self.od.unit)
        return value

    @phys.setter
    def phys(self, value):
        self.raw = self.od.encode_phys(value)

    @property
    def desc(self):
        """Converts to and from a description of the value as a string."""
        value = self.od.decode_desc(self.raw)
        logger.debug("Description is '%s'", value)
        return value

    @desc.setter
    def desc(self, desc):
        self.raw = self.od.encode_desc(desc)

    @property
    def bits(self):
        """Access bits using integers, slices, or bit descriptions."""
        return self._bits


class Bits(object):

    def __init__(self, variable):
        self.variable = variable

    def _get_bits(self, key):
        if isinstance(key, slice):
            bits = range(key.start, key.stop, key.step)
        elif isinstance(key, int):
            bits = [key]
        else:
            bits = key
        return bits

    def __getitem__(self, key):
        return self.variable.od.decode_bits(self.variable.raw,
                                            self._get_bits(key))

    def __setitem__(self, key, value):
        self.variable.raw = self.variable.od.encode_bits(
            self.variable.raw, self._get_bits(key), value)
