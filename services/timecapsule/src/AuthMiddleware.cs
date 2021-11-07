using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

namespace timecapsule
{
	public class AuthMiddleware
	{
		public AuthMiddleware(RequestDelegate next) => this.next = next;

		public async Task Invoke(HttpContext context)
		{
			var container = await TryAuthFromCookie(context);
			if(container?.Author != null) context.User = new ClaimsPrincipal(new ClaimsIdentity(new Claim[] { new(ClaimTypes.Name, container.Author) }));

			await next.Invoke(context).ConfigureAwait(false);
		}

		public static async Task SetAuthCookie(HttpContext context, Container user)
			=> context.Response.Cookies.Append(AuthCookieName, await TimeCapsuleWrapper.WrapAsync(user, context.RequestAborted));

		public static async Task<Container> TryAuthFromCookie(HttpContext context)
		{
			var cookie = context.Request.Cookies[AuthCookieName];
			if(string.IsNullOrEmpty(cookie))
				return null;
			try { return await TimeCapsuleWrapper.UnwrapAsync(cookie, context.RequestAborted); } catch { return null; }
		}

		private const string AuthCookieName = "auth";
		private readonly RequestDelegate next;
	}

	public static class AuthMiddlewareExtensions
	{
		public static IApplicationBuilder UseAuth(this IApplicationBuilder builder)
			=> builder.UseMiddleware<AuthMiddleware>();
	}
}
