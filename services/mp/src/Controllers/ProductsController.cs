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
        public IActionResult Get(string id)
        {
            var result = GetInternal(id);
            if (result == null)
                return BadRequest(NotFound($"Can't find product with id {id}"));
            return Ok(ProductModel.FromDocument(result));
        }

        [HttpGet("search")]
        public IActionResult Search([FromQuery] string query, DateTime? clientDt)
        {
	        try
	        {
		        return Ok(SearchInternal(query, clientDt).Where(document => document.IsProduct()).Select(ProductModel.FromDocument).ToArray());
            }
	        catch (ApiException ex)
	        {
		        return BadRequest(new { message = ex.Message });
	        }
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
