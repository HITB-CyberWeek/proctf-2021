/* This file is auto-generated by brotoc.
 * It's like protoc, but much more cooler. */
#ifndef _TREE_HPP_
#define _TREE_HPP_
#include "broto.hpp"
#include "person.hpp"
#include <optional>
#include <vector>
namespace brotobuf {
class GenealogyTree : public _AbstractMessage {
public:
  unsigned long long id;
  std::string title;
  std::string description;
  std::vector<unsigned long long> owners;
  std::optional<Person> person;
  GenealogyTree();
  void serialize(OutputStream &stream) const;
  void serialize(OutputStream &&stream) const;
  void deserialize(InputStream &stream);
  void deserialize(InputStream &&stream);

private:
  std::vector<unsigned long long>::iterator _owners_iterator;
  void serialize_id(OutputStream &stream) const;
  void serialize_title(OutputStream &stream) const;
  void serialize_description(OutputStream &stream) const;
  void serialize_owners(OutputStream &stream) const;
  void serialize_person(OutputStream &stream) const;
};
} // namespace brotobuf
#endif