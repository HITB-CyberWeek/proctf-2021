using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace mp.Entities
{
    public class JoinField
    {
        [JsonProperty("name")] public string RelationName;
        [JsonProperty("parent", DefaultValueHandling = DefaultValueHandling.Ignore)] public string ParentId;

        public const string ProductRelationName = "product";
        public const string OrderRelationName = "order";

        public static JoinField Product() => new JoinField {RelationName = ProductRelationName };
        public static JoinField Order(string parentId) => new JoinField {ParentId = parentId, RelationName = "order"};
    }
}
