using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using mp.Services;

namespace mp.Controllers
{
    [Authorize]
    [ApiController]
    [Route("api/[controller]")]
    public class ProductsController : ControllerBase
    {
        private readonly OpenSearchService openSearchService;

        // GET: api/<Products>
        [HttpGet("search")]
        public string Search([FromQuery] string query)
        {
            return openSearchService.Search(query).Result;
        }

        // GET api/<Products>/5
        [HttpGet("{id}")]
        public string Get(int id)
        {
            return "value";
        }

        // PUT api/<Products>/5
        [HttpPut("{id}")]
        public void Put(int id, [FromBody] string value)
        {
        }

        // DELETE api/<Products>/5
        [HttpDelete("{id}")]
        public void Delete(int id)
        {
        }

        public ProductsController(OpenSearchService openSearchService)
        {
            this.openSearchService = openSearchService;
        }
    }
}
