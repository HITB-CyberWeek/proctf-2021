using System;
using Microsoft.AspNetCore.Mvc;
using System.Linq;
using Microsoft.AspNetCore.Authorization;
using mp.Entities;
using mp.Models.Searchable;
using mp.Services;

namespace mp.Controllers
{
    [Authorize]
    [ApiController]
    [Route("api/[controller]")]
    public class ProductsController : SearchController
    {
        [HttpGet("{id}")]
        public ProductModel Get(string id)
        {
            return ProductModel.FromDocument(GetInternal(id));
        }

        [HttpGet("search")]
        public ProductModel[] Search([FromQuery] string query, int pageNum)
        {
            return SearchInternal(query, pageNum).Where(document => document.IsProduct()).Select(ProductModel.FromDocument).ToArray();
        }

        [HttpPut("create")]
        public IActionResult CreateProduct([FromBody] ProductModel product)
        {
            return Ok(openSearchService.IndexDocumentAsync(Document.CreateProduct(product.Name, product.Description, creator: HttpContext?.User.FindCurrentUserId())).Result);
        }

        public ProductsController(OpenSearchService openSearchService) : base(openSearchService)
        {
        }
    }
}
