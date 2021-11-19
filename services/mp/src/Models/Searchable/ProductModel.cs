using System;
using mp.Entities;

namespace mp.Models.Searchable
{
    public class ProductModel
    {
	    [SwaggerIgnore] public string Id { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        [SwaggerIgnore] public string Creator { get; set; }
        [SwaggerIgnore] public DateTime Dt { get; set; }

        public static ProductModel FromDocument(Document document)
        {
            if(document == null || !document.IsProduct())
                return null;

            return new ProductModel
            {
                Id = document.Id,
                Name = document.Name,
                Description = document.Text,
                Creator = document.Creator,
                Dt = document.Dt
            };
        }
    }
}
