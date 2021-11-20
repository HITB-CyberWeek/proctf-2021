using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.AspNetCore;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.Extensions;
using Microsoft.AspNetCore.Mvc;
using OpenIddict.Abstractions;
using OpenIddict.Server.AspNetCore;

namespace OAuthServer.Controllers
{
    public class AuthorizationController : Controller
    {
        private readonly ITokenIssueRateManager rateManager;

        public AuthorizationController(ITokenIssueRateManager rateManager)
        {
            this.rateManager = rateManager;
        }

        [HttpGet("~/connect/authorize")]
        [HttpPost("~/connect/authorize")]
        [IgnoreAntiforgeryToken]
        public async Task<IActionResult> Authorize()
        {
            var request = HttpContext.GetOpenIddictServerRequest() ??
                          throw new InvalidOperationException("The OpenID Connect request cannot be retrieved.");

            // Retrieve the user principal stored in the authentication cookie.
            var result = await HttpContext.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);

            // If the user principal can't be extracted, redirect the user to the login page.
            if (!result.Succeeded)
            {
                var redirectUri = Request.PathBase + Request.Path + QueryString.Create(Request.HasFormContentType ? Request.Form.ToList() : Request.Query.ToList());
                return Challenge(authenticationSchemes: CookieAuthenticationDefaults.AuthenticationScheme,
                                 properties: new AuthenticationProperties
                                             {
                                                 RedirectUri = redirectUri
                                             });
            }

            var clientId = request.ClientId;
            var instanceId = Request.Query["app_id"].FirstOrDefault();
            if (instanceId == null)
            {
                return BadRequest("app_id parameter is missing");
            }

            var userId = result.Principal.GetClaim(ClaimTypes.NameIdentifier);
            var groupId = result.Principal.GetClaim(ClaimTypes.GroupSid);
            var username = result.Principal.GetClaim(ClaimTypes.Name);

            if (!rateManager.TryIssueToken(clientId, instanceId, groupId, out var reason, out var left))
            {
                if (reason == RejectionReason.NotFound)
                {
                    return NotFound($"Unknown client_id {clientId}");
                }

                return RedirectToAction("Index", "Wait",
                    new
                    {
                        left = (int) Math.Ceiling(left.TotalSeconds),
                        redirect_uri = HttpContext.Request.GetEncodedUrl()
                    });
            }

            var claims = new List<Claim>
            {
                new Claim(OpenIddictConstants.Claims.Subject, userId),
                new Claim(OpenIddictConstants.Claims.Username, username).SetDestinations(OpenIddictConstants
                    .Destinations.AccessToken),
                new Claim("app_id", instanceId).SetDestinations(OpenIddictConstants.Destinations.AccessToken)
            };

            var claimsIdentity = new ClaimsIdentity(claims, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);

            var claimsPrincipal = new ClaimsPrincipal(claimsIdentity);

            // Signing in with the OpenIddict authentiction scheme trigger OpenIddict to issue a code (which can be exchanged for an access token)
            return SignIn(claimsPrincipal, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
        }

        [HttpPost("~/connect/token")]
        [Produces("application/json")]
        public async Task<IActionResult> Exchange()
        {
            var request = HttpContext.GetOpenIddictServerRequest() ??
                          throw new InvalidOperationException("The OpenID Connect request cannot be retrieved.");

            if (!request.IsAuthorizationCodeGrantType())
            {
                return BadRequest("The specified grant type is not supported.");
            }

            // Retrieve the claims principal stored in the authorization code
            var claimsPrincipal = (await HttpContext.AuthenticateAsync(OpenIddictServerAspNetCoreDefaults.AuthenticationScheme)).Principal;

            // Returning a SignInResult will ask OpenIddict to issue the appropriate access/identity tokens.
            return SignIn(claimsPrincipal, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
        }
    }
}