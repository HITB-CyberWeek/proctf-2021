using System;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http.Extensions;
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

        private const int ThrottlingLimit = 2;
        private static int ConcurrentSearchRequestsCount;

        protected IEnumerable<Document> SearchInternal(string query, int pageNum, DateTime? clientDt)
        {
            try
            {
                var currentRequestsInProcess = Interlocked.Increment(ref ConcurrentSearchRequestsCount);
                if(currentRequestsInProcess > ThrottlingLimit)
                {
                    if(clientDt == null)
	                    throw new ApiException("Throttling is on, but POW not satisfied");

                    var utcNow = DateTime.UtcNow;
                    if(clientDt > utcNow.AddSeconds(10) || clientDt < utcNow.AddSeconds(-10))
	                    throw new ApiException($"Client dt {clientDt.Value:s} is not synced with service dt {utcNow:s}");

                    if (!IsProofOfWorkValid())
		                throw new ApiException($"Proof of work is invalid");
                }
                return SearchInternalWithoutPOW(query, pageNum);
            }
            finally
            {
                Interlocked.Decrement(ref ConcurrentSearchRequestsCount);
            }
        }

        protected IEnumerable<Document> SearchInternalWithoutPOW(string query, int pageNum)
        {
	        return openSearchService.SearchAsync(query, pageNum).Result;
        }

        private bool IsProofOfWorkValid()
        {
	        if(HttpContext.Request.QueryString.Value == null)
		        return false;

	        var buf = Encoding.ASCII.GetBytes(HttpContext.Request.Host + HttpContext.Request.QueryString.Value!);
            var hash = new SHA512Managed().ComputeHash(buf);
	        return hash[0] == 0 && hash[1] == 0 && (hash[2] & 0b11000000) == 0;
        }

        protected Document GetInternal(string id)
        {
            return openSearchService.TryGet(id).Result;
        }

        public SearchController(OpenSearchService openSearchService)
        {
            this.openSearchService = openSearchService;
        }
    }
}
