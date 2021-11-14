// Copyright (c) 2016-2021 Dr. Colin Hirsch and Daniel Frey
// Please see LICENSE for license or visit https://github.com/taocpp/json/

#ifndef TAO_JSON_JAXN_EVENTS_TO_STRING_HPP
#define TAO_JSON_JAXN_EVENTS_TO_STRING_HPP

#include <sstream>
#include <string>
#include <utility>

#include "to_stream.hpp"

namespace tao::json::jaxn::events
{
   // Events consumer to build a JAXN string representation.

   struct to_string
      : to_stream
   {
      std::ostringstream oss;

      to_string()
         : to_stream( oss )
      {}

      [[nodiscard]] std::string value() const&
      {
         return oss.str();
      }

      [[nodiscard]] std::string value() &&
      {
         return std::move( oss ).str();
      }
   };

}  // namespace tao::json::jaxn::events

#endif
