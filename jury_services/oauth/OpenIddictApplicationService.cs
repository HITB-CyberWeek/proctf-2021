using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using OAuthServer.Configuration;
using OpenIddict.Abstractions;

namespace OAuthServer
{
    public class OpenIddictApplicationService : IHostedService
    {
        private readonly IServiceProvider serviceProvider;
        private readonly ApplicationConfiguration[] appConfigs;

        public OpenIddictApplicationService(IServiceProvider serviceProvider)
        {
            this.serviceProvider = serviceProvider;
            appConfigs = serviceProvider.GetRequiredService<IConfiguration>().GetSection("Applications")
                .Get<ApplicationConfiguration[]>();
        }

        public async Task StartAsync(CancellationToken cancellationToken)
        {
            using var scope = serviceProvider.CreateScope();

            var context = scope.ServiceProvider.GetRequiredService<DbContext>();
            await context.Database.EnsureCreatedAsync(cancellationToken);

            var manager = scope.ServiceProvider.GetRequiredService<IOpenIddictApplicationManager>();

            foreach (var appConfig in appConfigs)
            {
                await manager.CreateAsync(new OpenIddictApplicationDescriptor
                {
                    ClientId = appConfig.ClientId,
                    // TODO clean permissions
                    Permissions =
                    {
                        OpenIddictConstants.Permissions.Endpoints.Authorization,
                        OpenIddictConstants.Permissions.Endpoints.Token,

                        OpenIddictConstants.Permissions.GrantTypes.AuthorizationCode,
                        OpenIddictConstants.Permissions.GrantTypes.ClientCredentials,

                        OpenIddictConstants.Permissions.Prefixes.Scope + "api",

                        OpenIddictConstants.Permissions.ResponseTypes.Code
                    }
                }, cancellationToken);
            }
        }

        public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;
    }
}