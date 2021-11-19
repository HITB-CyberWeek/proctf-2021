using System;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using Microsoft.AspNetCore.Authorization;
using mp.Entities;
using mp.Services;

namespace mp.Controllers
{
    [Authorize]
    [ApiController]
    [Route("api/[controller]")]
    public class SearchController : ControllerBase
    {
        protected readonly OpenSearchService openSearchService;

        protected IEnumerable<Document> SearchInternal(string query, int pageNum)
        {
            return openSearchService.SearchAsync(query, pageNum).Result;
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
