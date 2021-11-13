using System;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.AspNet.Identity;
using Microsoft.AspNetCore.Http;

namespace mp.Services
{
    public class OpenSearchService
    {
        private readonly IHttpContextAccessor httpContextAccessor;
        private readonly IUserService userService;
        private readonly ElasticClient elasticClient;

        public OpenSearchService(IHttpContextAccessor httpContextAccessor, IUserService userService, ElasticClient elasticClient)
        {
            this.httpContextAccessor = httpContextAccessor;
            this.userService = userService;
            this.elasticClient = elasticClient;
        }

        public async Task<string> Search(string queryString, int from = 0, int size = 10)
        {
            var userLogin = httpContextAccessor.HttpContext?.User.Identity?.GetUserId();
            var user = userService.Get(userLogin);
            return await elasticClient.SearchAsync(user, queryString, from, size);
        }
    }
}