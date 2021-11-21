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
    public class OrdersController : SearchController
    {
        [HttpGet("{id}")]
        public IActionResult Get(string id)
        {
            var result = GetInternal(id);
            if(result == null)
                return BadRequest(NotFound(""));
            return Ok(OrderModel.FromDocument(result));
        }

        [HttpGet("searchForMyProduct")]
        public IActionResult SearchForMyProduct([FromQuery] string productId, int pageNum)
        {
            if(productId == null)
                return BadRequest(new { message = $"{nameof(productId)} not specified" });

            return Ok(openSearchService.SearchOrdersOfProductAsync(productId, pageNum).Result.Where(document => document.IsOrder()).Select(OrderModel.FromDocument));
        }

        [HttpGet("search")]
        public OrderModel[] Search([FromQuery] string query, int pageNum)
        {
            return SearchInternal(query, pageNum).Where(document => document.IsOrder()).Select(OrderModel.FromDocument).ToArray();
        }

        [HttpPut("create")]
        public IActionResult CreateOrder([FromBody] OrderModel order)
        {
            var document = GetInternal(order.ProductId);
            if(document == null)
                return BadRequest(new { message = $"Product {order.ProductId} not found" });

            return Ok(openSearchService.IndexDocumentAsync(Document.CreateOrder(order.Description, document, creator: HttpContext?.User.FindCurrentUserId()), order.ProductId).Result);
        }

        public OrdersController(OpenSearchService openSearchService) : base(openSearchService)
        {
        }
    }
}
