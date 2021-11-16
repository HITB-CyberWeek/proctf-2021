using System;
using mp.Entities;

namespace mp.Models.Searchable
{
    public class OrderModel
    {
        public string Id { get; set; }
        public string ProductId { get; set; }
        public string Description { get; set; }
        public string Creator { get; set; }
        public DateTime Dt { get; set; }

        public static OrderModel FromDocument(Document document)
        {
            if (document == null || !document.IsOrder())
                return null;

            return new OrderModel
            {
                Id = document.Id,
                ProductId = document.JoinField.ParentId,
                Description = document.Text,
                Creator = document.Creator,
                Dt = document.Dt
            };
        }
    }
}
