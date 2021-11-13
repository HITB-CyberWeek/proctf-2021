using System;
using System.Text;
using System.Threading.Tasks;
using Elasticsearch.Net;
using Microsoft.AspNet.Identity;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.IdentityModel.Tokens;
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
            services.AddControllers();
            services.AddHttpContextAccessor();
            services.AddAutoMapper(AppDomain.CurrentDomain.GetAssemblies());

            // var appSettingsSection = Configuration.GetSection("AppSettings");
            // services.Configure<AppSettings>(appSettingsSection);
            // var appSettings = appSettingsSection.Get<AppSettings>();
            // var restApiJWTSecret = Encoding.ASCII.GetBytes(appSettings.RestApiJWTSecret);

            services.AddAuthentication(x =>
                {
                    // x.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
                    // x.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
                    x.DefaultAuthenticateScheme = CookieAuthenticationDefaults.AuthenticationScheme;
                    x.DefaultChallengeScheme = CookieAuthenticationDefaults.AuthenticationScheme;
                })
                .AddCookie(options =>
                {
                    options.Events = new CookieAuthenticationEvents
                    {
                        OnValidatePrincipal = async context =>
                        {
                            var userService = context.HttpContext.RequestServices.GetRequiredService<IUserService>();
                            var login = context.Principal?.Identity?.GetUserId();
                            var user = userService.Find(login);
                            if(user == null)
                            {
                                context.RejectPrincipal();
                                // await context.HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
                            }
                        }
                    };
                    // options.Cookie.IsEssential = true;
                    options.Cookie.Name = "mp";
                    options.Cookie.SecurePolicy = CookieSecurePolicy.None;
                    options.ExpireTimeSpan = TimeSpan.FromDays(7);
                    options.Cookie.HttpOnly = true;
                })
                // .AddJwtBearer(options =>
                // {
                //     options.Events = new JwtBearerEvents
                //     {
                //         OnTokenValidated = context =>
                //         {
                //             var userService = context.HttpContext.RequestServices.GetRequiredService<IUserService>();
                //             var login = context.Principal?.Identity?.Name;
                //             var user = userService.Find(login);
                //             if(user == null)
                //                 context.Fail("Unauthorized");
                //             return Task.CompletedTask;
                //         }
                //     };
                //     options.RequireHttpsMetadata = false;
                //     options.SaveToken = true;
                //     options.TokenValidationParameters = new TokenValidationParameters
                //     {
                //         ValidateIssuerSigningKey = true,
                //         IssuerSigningKey = new SymmetricSecurityKey(restApiJWTSecret),
                //         ValidateIssuer = false,
                //         ValidateAudience = false
                //     };
                // })
                ;

            services.AddSingleton<IUserService>(provider => new UserService("users"));
            services.AddSingleton(provider =>
            {
                var settings = new ConnectionConfiguration(new Uri("http://192.168.11.131:9200"))
                    .RequestTimeout(TimeSpan.FromSeconds(30))
                    .ThrowExceptions();
                var elasticLowLevelClient =  new ElasticLowLevelClient(settings);
                return new ElasticClient(elasticLowLevelClient, "mp");
            });
            services.AddSingleton<OpenSearchService>();

            services.AddSwaggerGen(c =>
            {
                c.SchemaFilter<DefaultsAwareSchemaFilter>();
                c.SwaggerDoc("v1", new OpenApiInfo {Title = "mp", Version = "v1"});

                // var jwtSecurityScheme = new OpenApiSecurityScheme
                // {
                //     Scheme = "bearer",
                //     BearerFormat = "JWT",
                //     Name = "JWT Authentication",
                //     In = ParameterLocation.Header,
                //     Type = SecuritySchemeType.Http,
                //     Reference = new OpenApiReference
                //     {
                //         Id = JwtBearerDefaults.AuthenticationScheme,
                //         Type = ReferenceType.SecurityScheme
                //     }
                // };
                // c.AddSecurityDefinition(jwtSecurityScheme.Reference.Id, jwtSecurityScheme);
                // c.AddSecurityRequirement(new OpenApiSecurityRequirement
                // {
                //     { jwtSecurityScheme, Array.Empty<string>() }
                // });
            });
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if(env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
                app.UseSwagger();
                app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "mp v1"));
            }

            app.UseRouting();

            app.UseAuthentication();
            app.UseAuthorization();

            app.UseEndpoints(endpoints => { endpoints.MapControllers(); });
        }
    }

    public class DefaultsAwareSchemaFilter : ISchemaFilter
    {
        public void Apply(OpenApiSchema schema, SchemaFilterContext context)
        {
            if (schema.Properties == null)
            {
                return;
            }

            foreach (var property in schema.Properties)
            {
                if (property.Value.Default != null && property.Value.Example == null)
                {
                    property.Value.Example = property.Value.Default;
                }
            }
        }
    }
}