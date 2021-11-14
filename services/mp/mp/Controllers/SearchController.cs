using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using mp.Entities;
using mp.Models.Searchable;
using mp.Services;

namespace mp.Controllers
{
    [Authorize]
    [ApiController]
    [Route("api/[controller]")]
    public class SearchController : ControllerBase
    {
        protected readonly OpenSearchService openSearchService;

        protected IEnumerable<Document> SearchInternal(string query)
        {
            return openSearchService.Search(query).Result;
        }

        protected Document GetInternal(string id)
        {
            return openSearchService.Get(id).Result;
        }

        public SearchController(OpenSearchService openSearchService)
        {
            this.openSearchService = openSearchService;
        }
    }
}
