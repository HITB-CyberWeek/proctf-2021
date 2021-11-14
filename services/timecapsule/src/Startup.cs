using System.Collections.Generic;
using System.IO;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.StaticFiles;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.FileProviders;

namespace timecapsule
{
	public class Startup
	{
		public void ConfigureServices(IServiceCollection services)
		{
			services.AddMvc();
			services.AddControllers().AddJsonOptions(options => options.JsonSerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull);
			services.AddEntityFrameworkSqlite().AddDbContext<DatabaseContext>();
		}

		public void Configure(IApplicationBuilder app)
		{
			DatabaseContext.Init();

			app
				.UseStatusCodePages("text/plain", "{0}")
				.UseDefaultFiles(new DefaultFilesOptions { DefaultFileNames = new List<string> { "index.html" } })
				.UseStaticFiles(new StaticFileOptions
				{
					ContentTypeProvider = new FileExtensionContentTypeProvider(),
					FileProvider = new PhysicalFileProvider(Path.Combine(Directory.GetCurrentDirectory(), "wwwroot")),
					ServeUnknownFileTypes = false
				})
				.UseAuth()
				.UseRouting()
				.UseEndpoints(endpoints => endpoints.MapControllers());
		}
	}
}
