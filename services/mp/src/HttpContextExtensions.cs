using System.Security.Claims;

namespace mp
{
    public static class HttpContextExtensions
    {
        public static string FindCurrentUserId(this ClaimsPrincipal claimsPrincipal)
        {
            return claimsPrincipal?.Identity?.Name;
        }
    }
}
