using System;
using System.IO;
using System.Threading.Tasks;
using Elasticsearch.Net;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.OpenApi.Models;
using mp.Services;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace mp
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        private IConfiguration Configuration { get; }

        public void ConfigureServices(IServiceCollection services)
        {
            services.AddControllers().AddNewtonsoftJson();
            services.AddHttpContextAccessor();

            services.AddDataProtection().PersistKeysToFileSystem(new DirectoryInfo("state/encryption/")).SetApplicationName(nameof(mp));

            services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
                .AddCookie(CookieAuthenticationDefaults.AuthenticationScheme, options =>
                {
                    options.Events = new CookieAuthenticationEvents
                    {
                        OnValidatePrincipal = context =>
                        {
                            var userService = context.HttpContext.RequestServices.GetRequiredService<UserService>();
                            var login = context.Principal?.FindCurrentUserId();
                            var user = userService.Find(login);
                            if(user == null) 
                                context.RejectPrincipal();
                            return Task.CompletedTask;
                        }
                    };
                    options.LoginPath = "/Users/whoami";
                    options.Cookie.Name = nameof(mp);
                    options.Cookie.SecurePolicy = CookieSecurePolicy.None;
                    options.ExpireTimeSpan = TimeSpan.FromDays(7);
                    options.Cookie.HttpOnly = true;
                });

            var usersStorage = new UsersStorage("state/users/");
            services.AddSingleton(provider => usersStorage);
            services.AddSingleton< UserService>();

            services.AddSingleton(provider =>
            {
                var settings = new ConnectionConfiguration(new Uri(Configuration["AppSettings:OpenSearchUrl"]))
                    .RequestTimeout(TimeSpan.FromSeconds(3))
                    .ThrowExceptions();
                var elasticLowLevelClient =  new ElasticLowLevelClient(settings);
                return new OpenSearchClient(elasticLowLevelClient, nameof(mp));
            });
            services.AddSingleton<OpenSearchService>();

            services.AddSwaggerGen(c =>
            {
                c.SchemaFilter<DefaultsAwareSchemaFilter>();
                c.SchemaFilter<SwaggerIgnoreFilter>();
                c.SwaggerDoc("v1", new OpenApiInfo {Title = nameof(mp), Version = "v1"});
            });
            services.AddSwaggerGenNewtonsoftSupport();
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            app.UseSwagger(options => options.SerializeAsV2 = true);
            app.UseSwaggerUI(c =>
            {
                c.RoutePrefix = "";
                c.SwaggerEndpoint("/swagger/v1/swagger.json", "mp v1");
                c.EnableTryItOutByDefault();
            });

            app.UseExceptionHandler(c => c.Run(async context =>
            {
                var exception = context.Features
                    .Get<IExceptionHandlerPathFeature>()
                    .Error;
                var id = DateTime.UtcNow.Ticks;
                await Console.Error.WriteLineAsync($"Unexpected exception occurred #{id}: {exception}");
                await context.Response.WriteAsJsonAsync(new {error = $"Unexpected error {id}"});
            }));

            app.UseRouting();

            app.UseAuthentication();
            app.UseAuthorization();

            app.UseEndpoints(endpoints => { endpoints.MapControllers(); });
        }
    }
}