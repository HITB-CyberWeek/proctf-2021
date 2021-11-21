/* This file is auto-generated by brotoc.
 * It's like protoc, but much more cooler. */
#include "tree.hpp"
#include "broto.hpp"
#include "person.hpp"

#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace brotobuf {
GenealogyTree::GenealogyTree() {
  this->title = "";
  this->description = "";
  this->owners = std::vector<unsigned long long>();
  this->person = {};
}
void GenealogyTree::serialize(OutputStream &stream) const {
  this->serialize(std::move(stream));
}
void GenealogyTree::serialize(OutputStream &&stream) const {
  if (this->_debug_memory_logs_enabled()) {
    printf("Starting serialization of GenealogyTree at %p\n", this);
  }
  this->serialize_id(stream);
  this->serialize_title(stream);
  this->serialize_description(stream);
  this->serialize_owners(stream);
  this->serialize_person(stream);
}
void GenealogyTree::deserialize(InputStream &stream) {
  this->deserialize(std::move(stream));
}
void GenealogyTree::deserialize(InputStream &&stream) {
  if (this->_debug_memory_logs_enabled()) {
    printf("== Starting deserialization of GenealogyTree at %p\n", this);
  }
  this->owners = std::vector<unsigned long long>();

  while (stream.has_next()) {
    unsigned long long field_index = this->_deserialize_varint(stream);
    switch (field_index) {

    case 0:
      if (this->_debug_memory_logs_enabled()) {
        printf("Deserializing data to id->id\n");
      }
      this->id = this->_deserialize_varint(stream);
      break;
    case 1:
      if (this->_debug_memory_logs_enabled()) {
        printf("Deserializing data to title->title\n");
      }
      this->_deserialize_string(this->title, stream);
      break;
    case 2:
      if (this->_debug_memory_logs_enabled()) {
        printf("Deserializing data to description->description\n");
      }
      this->_deserialize_string(this->description, stream);
      break;
    case 3:
      if (this->owners.empty()) {
        this->owners.resize(60);
        if (this->_debug_memory_logs_enabled()) {
          printf("Allocated %ld bytes for owner->owners at %p\n",
                 60 * sizeof(unsigned long long), owners.data());
        }
        this->_owners_iterator = this->owners.begin();
      }
      if (this->_debug_memory_logs_enabled()) {
        printf("Deserializing data to owner->owners[%ld]\n",
               this->_owners_iterator - this->owners.begin());
      }
      *(this->_owners_iterator) = this->_deserialize_varint(stream);
      this->_owners_iterator++;
      break;
    case 4:
      if (this->_debug_memory_logs_enabled()) {
        printf("Deserializing data to person->person\n");
      }
      this->person = Person();
      this->_deserialize_object<Person>(this->person.value(), stream);
      break;
    }
  }

  this->owners.resize(this->_owners_iterator - this->owners.begin());
  if (this->_debug_memory_logs_enabled()) {
    printf("Shrinking owner->owners, freeing %ld bytes at %p\n",
           owners.capacity() * sizeof(unsigned long long), owners.data());
  }
  this->owners.shrink_to_fit();
}
void GenealogyTree::serialize_id(OutputStream &stream) const {
  if (this->id == 0)
    return;
  this->_serialize_varint(0, stream);
  this->_serialize_varint(this->id, stream);
}
void GenealogyTree::serialize_title(OutputStream &stream) const {
  if (this->title == "")
    return;
  this->_serialize_varint(1, stream);
  this->_serialize_string(this->title, stream);
}
void GenealogyTree::serialize_description(OutputStream &stream) const {
  if (this->description == "")
    return;
  this->_serialize_varint(2, stream);
  this->_serialize_string(this->description, stream);
}
void GenealogyTree::serialize_owners(OutputStream &stream) const {
  if (this->owners.size() == 0)
    return;
  if (this->owners.size() > 60) {
    throw std::out_of_range(
        "Can not serialize object: owners is too long, max length is 60");
  }
  for (auto &element : this->owners) {
    this->_serialize_varint(3, stream);
    this->_serialize_varint(element, stream);
  }
}
void GenealogyTree::serialize_person(OutputStream &stream) const {
  if (!this->person)
    return;
  this->_serialize_varint(4, stream);
  this->_serialize_object<Person>(this->person.value(), stream);
}
} // namespace brotobuf