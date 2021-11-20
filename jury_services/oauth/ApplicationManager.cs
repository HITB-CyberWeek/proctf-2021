using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using OAuthServer.Configuration;
using OpenIddict.Abstractions;
using OpenIddict.Core;
using OpenIddict.EntityFrameworkCore.Models;

namespace OAuthServer
{
    public class ApplicationManager<TApplication> : OpenIddictApplicationManager<TApplication>
        where TApplication : class
    {
        private readonly Dictionary<string, Regex> redirectUriRegexes;

        public ApplicationManager(IOpenIddictApplicationCache<TApplication> cache,
            ILogger<OpenIddictApplicationManager<TApplication>> logger, IOptionsMonitor<OpenIddictCoreOptions> options,
            IOpenIddictApplicationStoreResolver resolver, IConfiguration configuration) : base(cache, logger, options,
            resolver)
        {
            redirectUriRegexes = configuration.GetSection("Applications").Get<ApplicationConfiguration[]>()
                .ToDictionary(c => c.ClientId, c => new Regex(c.RedirectUriRegex));
        }

        public override ValueTask<bool> ValidateRedirectUriAsync(TApplication application, string address,
            CancellationToken cancellationToken = new CancellationToken())
        {
            var clientId = (application as OpenIddictEntityFrameworkCoreApplication)?.ClientId;
            if (clientId != null && redirectUriRegexes.TryGetValue(clientId, out var regex))
            {
                return new ValueTask<bool>(regex.IsMatch(address));
            }

            return new ValueTask<bool>(false);
        }
    }
}