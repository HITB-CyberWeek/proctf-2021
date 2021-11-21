from dataclasses import dataclass
from typing import TypeVar, Any, Iterable, Union, Callable

from streams import InputStream, OutputStream

T = TypeVar("T")
V = TypeVar("V")


@dataclass
class FieldType:
    cpp_type = NotImplementedError

    constructor_value = None

    def dump(self, value: Any, stream: OutputStream):
        raise NotImplementedError

    def parse(self, stream: InputStream) -> Any:
        raise NotImplementedError

    def generate_serialization_statement(self, variable_name: str) -> Iterable[str]:
        raise NotImplementedError

    def generate_deserialization_statement(self, variable_name: str) -> Iterable[str]:
        raise NotImplementedError

    def generate_default_value_comparison_statement(self, variable_name: str) -> str:
        raise NotImplementedError


class VarInt(FieldType):
    """
    Only non-negative numbers supported
    """
    MSB = 1 << 7

    cpp_type = "unsigned long long"

    constructor_value = None  # don't initialize numbers for vulnerability

    def generate_serialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"this->_serialize_varint({variable_name}, stream);"

    def generate_deserialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"{variable_name} = this->_deserialize_varint(stream);"

    def generate_default_value_comparison_statement(self, variable_name: str) -> str:
        return f"{variable_name} == 0"

    def dump(self, value: int, stream: OutputStream):
        assert value >= 0

        binary = format(value, "b")

        binary_length = len(binary)
        if binary_length % 7 != 0:
            binary_length += 7 - binary_length % 7
        binary = binary.zfill(binary_length)

        result = []
        for idx in range(0, binary_length, 7):
            piece = int(binary[idx:idx + 7], 2)
            if idx == 0:
                result.append(piece)
            else:
                result.append(self.MSB | piece)

        stream.write(bytes(reversed(result)))

    def parse(self, stream: InputStream) -> int:
        b: list[int] = []
        while stream.next & self.MSB:
            b.append(stream.read_byte() & ~self.MSB)
        b.append(stream.read_byte())
        return int("".join(format(byte, "b").zfill(7) for byte in reversed(b)), 2)


class String(FieldType):
    cpp_type = "std::string"

    constructor_value = '""'

    def generate_serialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"this->_serialize_string({variable_name}, stream);"

    def generate_deserialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"this->_deserialize_string({variable_name}, stream);"

    def generate_default_value_comparison_statement(self, variable_name: str):
        return f"{variable_name} == \"\""

    def dump(self, value: str, stream: OutputStream):
        VarInt().dump(len(value), stream)
        stream.write(value.encode())

    def parse(self, stream: InputStream) -> bytes:
        length = VarInt().parse(stream)
        return stream.read(length)
        # return stream.read(length).decode()


@dataclass
class Field:
    index: int
    name: str
    type: FieldType
    repeated: bool = False
    max_repeated: int = 10

    @property
    def cpp_type(self):
        if self.repeated:
            return f"std::vector< {self.type.cpp_type} >"
        return self.type.cpp_type

    @property
    def cpp_variable_name(self):
        if self.repeated:
            return self.name + "s"
        return self.name

    def generate_declaration(self) -> Iterable[str]:
        yield f"{self.cpp_type} {self.cpp_variable_name};"

    def generate_constructor_statements(self) -> Iterable[str]:
        if self.repeated:
            yield f"this->{self.cpp_variable_name} = {self.cpp_type}();"
        else:
            if self.type.constructor_value is not None:
                yield f"this->{self.cpp_variable_name} = {self.type.constructor_value};"

    def generate_serialization_statements(self) -> Iterable[str]:
        if self.repeated:
            yield f"for (auto& element: this->{self.cpp_variable_name}) {{"
            yield f"    this->_serialize_varint({self.index}, stream);"
            yield from self.type.generate_serialization_statement("element")
            yield "}"
        else:
            yield f"this->_serialize_varint({self.index}, stream);"
            yield from self.type.generate_serialization_statement("this->" + self.cpp_variable_name)

    def generate_pre_deserialization_statements(self) -> Iterable[str]:
        if self.repeated:
            yield f"this->{self.cpp_variable_name} = {self.cpp_type}();"

    def generate_deserialization_statements(self) -> Iterable[str]:
        if self.repeated:
            yield f"if (this->{self.cpp_variable_name}.empty()) {{"
            yield f"this->{self.cpp_variable_name}.resize({self.max_repeated});"
            yield "if (this->_debug_memory_logs_enabled()) {"
            yield f'printf("Allocated %ld bytes for {self.name}->{self.cpp_variable_name} at %p\\n", {self.max_repeated} * sizeof({self.type.cpp_type}), {self.cpp_variable_name}.data());'
            yield "}"
            yield f"this->_{self.cpp_variable_name}_iterator = this->{self.cpp_variable_name}.begin();"
            yield "}"

            yield "if (this->_debug_memory_logs_enabled()) {"
            yield f'printf("Deserializing data to {self.name}->{self.cpp_variable_name}[%ld]\\n", this->_{self.cpp_variable_name}_iterator - this->{self.cpp_variable_name}.begin());'
            yield "}"
            yield from self.type.generate_deserialization_statement(f"*(this->_{self.cpp_variable_name}_iterator)")
            yield f"this->_{self.cpp_variable_name}_iterator++;"
        else:
            yield "if (this->_debug_memory_logs_enabled()) {"
            yield f'printf("Deserializing data to {self.name}->{self.cpp_variable_name}\\n");'
            yield "}"
            yield from self.type.generate_deserialization_statement('this->' + self.cpp_variable_name)

    def generate_post_deserialization_statements(self) -> Iterable[str]:
        if self.repeated:
            yield f"this->{self.cpp_variable_name}.resize(this->_{self.cpp_variable_name}_iterator - this->{self.cpp_variable_name}.begin());"
            yield "if (this->_debug_memory_logs_enabled()) {"
            yield f'printf("Shrinking {self.name}->{self.cpp_variable_name}, freeing %ld bytes at %p\\n", {self.cpp_variable_name}.capacity() * sizeof({self.type.cpp_type}), {self.cpp_variable_name}.data());'
            yield "}"
            yield f"this->{self.cpp_variable_name}.shrink_to_fit();"

    def generate_default_value_comparison_statement(self) -> str:
        if self.repeated:
            return f"this->{self.cpp_variable_name}.size() == 0"
        else:
            return self.type.generate_default_value_comparison_statement(f"this->{self.cpp_variable_name}")

    def generate_pre_serialization_statements(self) -> Iterable[str]:
        if self.repeated:
            yield f"if (this->{self.cpp_variable_name}.size() > {self.max_repeated}) {{"
            yield f'    throw std::out_of_range("Can not serialize object: {self.cpp_variable_name} is too long, max length is {self.max_repeated}");'
            yield "}"


@dataclass
class Message(FieldType):
    name: str
    fields: list[Field]

    def dump(self, value: dict, stream: OutputStream):
        for field in self.fields:
            if field.name in value:
                VarInt().dump(field.index, stream)
                field.type.dump(value[field.name], stream)

    def dump_dict(self, value: dict) -> bytes:
        stream = OutputStream()
        self.dump(value, stream)
        return stream.s

    def dump_list(self, values: list[tuple[str, Any]]) -> bytes:
        stream = OutputStream()
        field_by_name: dict[str, (int, Field)] = {field.name: field for field in self.fields}
        for field_name, field_value in values:
            if field_name in field_by_name:
                field = field_by_name[field_name]
                VarInt().dump(field.index, stream)
                field.type.dump(field_value, stream)
        return stream.s

    def parse(self, data: bytes) -> dict:
        stream = InputStream(data)
        result = {}
        field_by_index: dict[int, Field] = {field.index: field for field in self.fields}
        while stream.has_next:
            field_number = VarInt().parse(stream)
            assert field_number in field_by_index

            field = field_by_index[field_number]
            value = field.type.parse(stream)

            if not field.repeated:
                result[field.name] = value
            else:
                if field.name not in result:
                    result[field.name] = []
                result[field.name].append(value)

        return result

    def generate_common_header_file(self) -> Iterable[str]:
        code = """
        #include <vector>
        #include <string>
        #include <stdexcept>
        #include <memory>
        #include <tuple>
        
        namespace brotobuf {

        class InputStream {
            using iterator = std::vector<unsigned char>::iterator;
        public:
            InputStream(const iterator & begin, const iterator & end);
            unsigned char read_byte();
            std::tuple<iterator, iterator> read_chunk(size_t count);
            bool has_next() const;
        private:
            iterator _iterator;
            iterator _end;
        };

        class OutputStream {
        public:
            OutputStream();
            void write(unsigned char c);
            void write(const std::vector <unsigned char> && data);
            std::vector<unsigned char> get() const;
        private:
            std::vector<unsigned char> buffer;    
        };

        class _AbstractMessage {
        protected:
            void _serialize_varint(unsigned long long variable, OutputStream & stream) const;
            void _serialize_string(const std::string & variable, OutputStream & stream) const;
            template <typename T> void _serialize_object(const T & variable, OutputStream & stream) const {
                auto temp_stream = OutputStream();
                variable.serialize(temp_stream);
                auto data = temp_stream.get();

                this->_serialize_varint(data.size(), stream);
                stream.write(std::move(data));
            }
            unsigned long long _deserialize_varint(InputStream & stream);
            void _deserialize_string(std::string & variable, InputStream & stream);
            template <typename T> void _deserialize_object(T & variable, InputStream & stream) {
                auto length = this->_deserialize_varint(stream);
                auto [from, to] = stream.read_chunk(length);
                auto temp_stream = InputStream(from, to);

                variable.deserialize(temp_stream);
            }
            bool _debug_memory_logs_enabled() const;
        };
        
        }
        """
        yield from code.splitlines()

    def generate_header_file(self) -> Iterable[str]:
        yield "#include <vector>"
        yield "#include <optional>"

        yield "namespace brotobuf {"

        yield f"class {self.name}: public _AbstractMessage {{"
        yield "public:"

        # Fields
        for field in self.fields:
            yield from field.generate_declaration()

        # Constructor
        yield f"{self.name}();"

        yield "void serialize(OutputStream& stream) const;"
        yield "void serialize(OutputStream&& stream) const;"
        yield "void deserialize(InputStream& stream);"
        yield "void deserialize(InputStream&& stream);"

        yield "private:"

        for field in self.fields:
            if field.repeated:
                yield f"{field.cpp_type}::iterator _{field.cpp_variable_name}_iterator;"

        # Serialize_* methods
        for field in self.fields:
            yield f"void serialize_{field.cpp_variable_name}(OutputStream& stream) const;"

        yield "};"

        yield "}"

    def generate_common_implementation(self) -> Iterable[str]:
        code = """
#include <vector>
#include <string>
#include <stdexcept>
#include <memory>
#include <tuple>
#include <cstring>

namespace brotobuf {

InputStream::InputStream(const std::vector<unsigned char>::iterator & begin, const std::vector<unsigned char>::iterator & end) {
    if (end - begin > 10000) {
        throw std::out_of_range("Too large message, can't deserialize it");
    }
    this->_iterator = begin;
    this->_end = end;
}
    
unsigned char InputStream::read_byte() {
    if (!this->has_next()) {
        throw std::out_of_range("Input stream reached its end");
    }
    return *(this->_iterator++);
}

std::tuple<InputStream::iterator, InputStream::iterator> InputStream::read_chunk(size_t count) {
    if (this->_end - this->_iterator < (long long) count) {
        throw std::out_of_range("Input stream reached its end");
    }
    auto start_iterator = this->_iterator;
    this->_iterator += count;
    return {start_iterator, this->_iterator};
}
    
bool InputStream::has_next() const {
    return this->_iterator != this->_end;
}
    
OutputStream::OutputStream() {
    buffer = std::vector<unsigned char>();
}
    
void OutputStream::write(unsigned char c) {
    buffer.push_back(c);
}
    
void OutputStream::write(const std::vector<unsigned char>&& data) {
    buffer.insert(buffer.end(), data.begin(), data.end());
}
    
std::vector<unsigned char> OutputStream::get() const {
    return buffer;
}

void _AbstractMessage::_serialize_varint(unsigned long long variable, OutputStream& stream) const {
    unsigned long long value = variable;
    do {
        unsigned char last_bits = value & 0x7f;
        value >>= 7;
        if (value) {
            last_bits |= 1 << 7;
        }
        stream.write(last_bits);
    } while (value);
}
    
void _AbstractMessage::_serialize_string(const std::string & variable, OutputStream& stream) const {
    this->_serialize_varint(variable.length(), stream);
    for (auto& c: variable) {
        stream.write((unsigned char) c);
    }
}
    
unsigned long long _AbstractMessage::_deserialize_varint(InputStream& stream) {
    unsigned long long result = 0;
    unsigned char byte = stream.read_byte();
    size_t shift = 0;
    while (byte & (1 << 7)) {
        result |= ((unsigned long long) (byte & 0x7f)) << shift;
        byte = stream.read_byte();
        shift += 7;
        if (shift > 56) {
            throw std::out_of_range("Too large varint in the stream");
        }
    }
    result |= ((unsigned long long) byte) << shift;
    return result;
}
    
void _AbstractMessage::_deserialize_string(std::string & variable, InputStream& stream) {
    unsigned long long length = this->_deserialize_varint(stream);
    variable.resize(length);
    for (size_t i = 0; i < length; i++) {
        variable[i] = stream.read_byte();
    }
}    

bool _AbstractMessage::_debug_memory_logs_enabled() const {
    const auto env = getenv("BROTOBUF_DEBUG_MEMORY");
    if (!env) {
        return false;
    }
    return strncmp(env, "1", 1) == 0;
}

}
        """
        yield from code.splitlines()

    def generate_code(self) -> Iterable[str]:
        code = """
#include <vector>
#include <string>
#include <stdexcept>
#include <memory>
#include <tuple>
#include <optional>
        """
        yield from code.splitlines()

        yield "namespace brotobuf {"

        # Constructor
        yield f"{self.name}::{self.name}() {{"
        for field in self.fields:
            yield from field.generate_constructor_statements()
        yield "}"

        # Serialize
        yield f"void {self.name}::serialize(OutputStream& stream) const {{"
        yield "    this->serialize(std::move(stream));"
        yield "}"

        yield f"void {self.name}::serialize(OutputStream&& stream) const {{"
        yield "if (this->_debug_memory_logs_enabled()) {"
        yield f'printf("Starting serialization of {self.name} at %p\\n", this);'
        yield "}"
        for field in self.fields:
            yield f"    this->serialize_{field.cpp_variable_name}(stream);"
        yield "}"

        # Deserialize
        yield f"void {self.name}::deserialize(InputStream& stream) {{"
        yield "    this->deserialize(std::move(stream));"
        yield "}"

        yield f"void {self.name}::deserialize(InputStream&& stream) {{"
        yield "if (this->_debug_memory_logs_enabled()) {"
        yield f'printf("== Starting deserialization of {self.name} at %p\\n", this);'
        yield "}"
        for field in self.fields:
            yield from field.generate_pre_deserialization_statements()
        yield """
while (stream.has_next()) {
    unsigned long long field_index = this->_deserialize_varint(stream);
    switch (field_index) {
        """
        for field in self.fields:
            yield f"    case {field.index}: "
            yield from field.generate_deserialization_statements()
            yield "    break;"
        yield """
    }
}        
"""
        for field in self.fields:
            yield from field.generate_post_deserialization_statements()

        yield "}"

        # Serialize
        for field in self.fields:
            yield f"void {self.name}::serialize_{field.cpp_variable_name}(OutputStream& stream) const {{"
            yield f"if ({field.generate_default_value_comparison_statement()}) return;"
            yield from field.generate_pre_serialization_statements()
            yield from field.generate_serialization_statements()
            yield "}"

        yield "}"


@dataclass
class SharedPtrField(FieldType):
    message: Union[Message, Callable[[], Message]]

    @property
    def message_class(self):
        if isinstance(self.message, Message):
            return self.message
        return self.message()

    @property
    def cpp_type(self) -> str:
        return f"std::shared_ptr<{self.message_class.name}>"

    @property
    def constructor_value(self) -> str:
        return f"{self.cpp_type}()"

    def dump(self, value: Any, stream: OutputStream):
        temp_stream = OutputStream()
        self.message_class.dump(value, temp_stream)

        VarInt().dump(len(temp_stream.s), stream)
        stream.write(temp_stream.s)

    def parse(self, stream: InputStream) -> Any:
        length = VarInt().parse(stream)
        data = stream.read(length)

        return self.message_class.parse(data)

    def generate_serialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"this->_serialize_object< {self.message_class.name} >(*{variable_name}, stream);"

    def generate_deserialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"{variable_name} = {self.cpp_type}(new {self.message_class.name}());"
        yield f"this->_deserialize_object< {self.message_class.name} >(*{variable_name}, stream);"

    def generate_default_value_comparison_statement(self, variable_name: str) -> str:
        return f"((bool) {variable_name}) == false"


@dataclass
class MessageField(SharedPtrField):
    @property
    def cpp_type(self):
        return self.message_class.name

    def generate_serialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"this->_serialize_object< {self.message_class.name} >({variable_name}, stream);"

    def generate_deserialization_statement(self, variable_name: str) -> Iterable[str]:
        yield f"this->_deserialize_object< {self.message_class.name} >({variable_name}, stream);"

    def generate_default_value_comparison_statement(self, variable_name: str) -> str:
        return "0"


@dataclass
class Optional(FieldType):
    field: FieldType

    @property
    def cpp_type(self):
        return f"std::optional< {self.field.cpp_type} >"

    @property
    def constructor_value(self) -> str:
        return "{}"

    def generate_serialization_statement(self, variable_name: str) -> Iterable[str]:
        yield from self.field.generate_serialization_statement(f"{variable_name}.value()")

    def generate_deserialization_statement(self, variable_name: str) -> Iterable[str]:
        constructor_value = self.field.constructor_value
        if isinstance(self.field, VarInt):
            constructor_value = "0"
        yield f"{variable_name} = {constructor_value};"
        yield from self.field.generate_deserialization_statement(f"{variable_name}.value()")

    def generate_default_value_comparison_statement(self, variable_name: str) -> str:
        return f"!{variable_name}"
