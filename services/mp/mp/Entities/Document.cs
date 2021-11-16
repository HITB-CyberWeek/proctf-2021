using System;
using mp.Models.Searchable;
using Newtonsoft.Json;

namespace mp.Entities
{
    public class Document
    {
        [JsonProperty("_id", DefaultValueHandling = DefaultValueHandling.Ignore)] public string Id { get; set; }
        [JsonProperty("product_name")] public string Name { get; internal set; }
        [JsonProperty("text")] public string Text { get; internal set; }
        [JsonProperty("created_by")] public string Creator { get; internal set; }
        [JsonProperty("readable_by", DefaultValueHandling = DefaultValueHandling.Ignore)] public string[] ReadableBy { get; internal set; }
        [JsonProperty("dt")] public DateTime Dt { get; internal set; }

        [JsonProperty("join_field", DefaultValueHandling = DefaultValueHandling.Ignore)] public JoinField JoinField { get; internal set; }

        public bool IsProduct()
        {
            return JoinField?.RelationName == JoinField.ProductRelationName;
        }

        public bool IsOrder()
        {
            return JoinField?.RelationName == JoinField.OrderRelationName;
        }

        public Document CloneAndSetId(string id)
        {
            var result = (Document)this.MemberwiseClone();
            result.JoinField = new JoinField
            {
                ParentId = JoinField.ParentId,
                RelationName = JoinField.RelationName
            };
            result.Id = id;
            return result;
        }

        public static Document CreateProduct(string name, string text, string creator)
        {
            return new Document
            {
                Name = name,
                Text = text,
                Creator = creator,
                Dt = DateTime.UtcNow,
                JoinField = JoinField.Product()
            };
        }

        public static Document CreateOrder(string text, Document product, string creator)
        {
            return new Document
            {
                Text = text,
                Creator = creator,
                ReadableBy = new[] {creator, product.Creator},
                Dt = DateTime.UtcNow,
                JoinField = JoinField.Order(product.Id)
            };
        }
    }
}
