using System;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.IdentityModel.Tokens;
using OpenIddict.Abstractions;
using OpenIddict.Core;
using OpenIddict.Server;

namespace OAuthServer
{
    public class Startup
    {
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddSingleton<ITokenManager, TokenManager>();
            services.AddSingleton<ITokenIssueRateManager, TokenIssueRateManager>();

            services.AddHostedService<OpenIddictApplicationService>();

            services.AddControllersWithViews();

            services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
                    .AddCookie(CookieAuthenticationDefaults.AuthenticationScheme, options =>
                    {
                        options.LoginPath = "/account/login";
                    });

            services.AddDbContext<DbContext>(options =>
            {
                options.UseInMemoryDatabase(nameof(DbContext));
                options.UseOpenIddict();
            });

            services.AddOpenIddict()
                .AddCore(options =>
                {
                    options.UseEntityFrameworkCore().UseDbContext<DbContext>();

                    options.Services.AddScoped(typeof(OpenIddictApplicationManager<>),
                        typeof(ApplicationManager<>));
                })
                .AddServer(options =>
                {
                    options.AllowAuthorizationCodeFlow()
                        .RequireProofKeyForCodeExchange();

                    var signingCert = new X509Certificate2("server.pfx", "",
                        X509KeyStorageFlags.Exportable | X509KeyStorageFlags.PersistKeySet);
                    var signingKey = new X509SecurityKey(signingCert);
                    var privateKeyBytes = signingCert.Export(X509ContentType.Pkcs12, "");
                    var keyBytes = new byte[256 >> 3];
                    Array.Copy(privateKeyBytes, keyBytes, keyBytes.Length);
                    var encryptionKey = new SymmetricSecurityKey(keyBytes);

                    options
                        .AddEncryptionKey(encryptionKey)
                        .AddSigningCertificate(signingCert);

                    options
                        .SetAuthorizationEndpointUris("/connect/authorize")
                        .SetTokenEndpointUris("/connect/token");

                    options
                        .UseAspNetCore()
                        .EnableTokenEndpointPassthrough()
                        .EnableAuthorizationEndpointPassthrough();

                    options.DisableAccessTokenEncryption();

                    options.AddEventHandler<OpenIddictServerEvents.ProcessSignInContext>(builder =>
                    {
                        // Make this event handler run just before GenerateIdentityModelAccessToken
                        builder.SetOrder(OpenIddictServerHandlers.GenerateIdentityModelAccessToken.Descriptor.Order - 1)
                            // Only run the event handler if an access token was generated
                            .AddFilter<OpenIddictServerHandlerFilters.RequireAccessTokenGenerated>()
                            .SetType(OpenIddict.Server.OpenIddictServerHandlerType.Custom)
                            .UseInlineHandler(context =>
                            {
                                // Clone the existing AccessTokenPrincipal without the private OpenIddict claims
                                context.AccessTokenPrincipal = context.AccessTokenPrincipal.Clone(claim =>
                                    claim.Type is not (
                                        OpenIddictConstants.Claims.Private.AuthorizationId or
                                        OpenIddictConstants.Claims.Private.Presenter or
                                        OpenIddictConstants.Claims.Private.TokenId
                                        ));
                                return default;
                            });
                    });
                });
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseStaticFiles();
            app.UseRouting();

            app.UseAuthentication();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapDefaultControllerRoute();
            });
        }
    }
}