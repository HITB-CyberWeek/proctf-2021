using Microsoft.AspNet.Identity;
using Microsoft.AspNetCore.Http;

namespace mp
{
    public static class HttpContextExtensions
    {
        public static string FindCurrentUserId(this HttpContext httpContext)
        {
            return httpContext?.User.Identity?.GetUserId();
        }
    }
}
