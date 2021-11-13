using System;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace timecapsule
{
	[ApiController]
	public class ApiController : ControllerBase
	{
		public ApiController(DatabaseContext dbCtx) => this.dbCtx = dbCtx;

		[HttpGet("auth")]
		public async Task<IActionResult> CheckAuth() => Ok(User?.Identity?.Name ?? string.Empty);

		[HttpPost("signup")]
		public async Task<IActionResult> SignUp(string login, string password)
		{
			if(string.IsNullOrEmpty(login) || string.IsNullOrEmpty(password) || login.Length < 3 || Encoding.UTF8.GetByteCount(login) > 255)
				return StatusCode(400, "bad login or password");

			var user = new UserContainer
			{
				Secret = ComputeHash(password),
				CreateDate = DateTime.UtcNow,
				Author = login.Trim().ToLower()
			};

			try
			{
				await dbCtx.Users.AddAsync(user, HttpContext.RequestAborted);
				await dbCtx.SaveChangesAsync(HttpContext.RequestAborted);
			}
			catch(DbUpdateException e) when (e.InnerException is SqliteException se && se.SqliteExtendedErrorCode == 1555)
			{
				return StatusCode(403, "user already exists");
			}

			await AuthMiddleware.SetAuthCookie(HttpContext, user);
			return Ok();
		}

		[HttpPost("signin")]
		public async Task<IActionResult> SignIn(string login, string password)
		{
			var user = await dbCtx.Users.FindAsync(new object[] { login?.Trim().ToLower() }, HttpContext.RequestAborted);
			if(user?.Secret == null || !SecureEquals(user.Secret.Value, ComputeHash(password)))
				return StatusCode(403, "user not found or bad password");

			user = new UserContainer
			{
				CreateDate = DateTime.UtcNow,
				Author = login?.Trim()
			};

			await AuthMiddleware.SetAuthCookie(HttpContext, user);
			return Ok();
		}

		[HttpGet("capsule/{id}")]
		public async Task<IActionResult> FindTimeCapsule(Guid id)
			=> Ok(RemoveSecretFields(await dbCtx.FindAsync<TextContainer>(id), User?.Identity?.Name, DateTime.UtcNow));

		[HttpPost("capsule")]
		public async Task<IActionResult> AddTimeCapsule(string text, DateTime toBeOpened)
		{
			var user = User?.Identity?.Name;
			if(user == null)
				return StatusCode(401, "not authenticated");

			if(string.IsNullOrEmpty(text = text?.Trim().ToLower()) || Encoding.UTF8.GetByteCount(text) > 255)
				return StatusCode(400, "text not specified or too large");

			var now = DateTime.UtcNow;
			if(toBeOpened < now)
				return StatusCode(400, "you can't send a capsule to the past");

			var capsule = new TextContainer
			{
				Id = SecureGuid(),
				Secret = SecureGuid(),
				CreateDate = now,
				ExpireDate = toBeOpened,
				Author = user,
				Text = text
			};

			await capsule.Wrap(HttpContext.RequestAborted);
			await dbCtx.Texts.AddAsync(capsule, HttpContext.RequestAborted);
			await dbCtx.SaveChangesAsync(HttpContext.RequestAborted);

			return Ok(capsule);
		}

		[HttpGet("capsules")]
		public async Task<IActionResult> FindTimeCapsules(string author)
		{
			var now = DateTime.UtcNow;
			var user = User?.Identity?.Name;

			var items = dbCtx.Texts
				.Where(text => string.IsNullOrEmpty(author) || text.Author == author)
				.OrderByDescending(text => text.CreateDate)
				.Take(100)
				.AsEnumerable()
				.With(text => RemoveSecretFields(text, user, now));

			return Ok(items);
		}

		private static TextContainer RemoveSecretFields(TextContainer capsule, string author, DateTime now)
		{
			if(capsule == null || capsule.ExpireDate <= now || capsule.Author == author)
				return capsule;

			capsule.Secret = null;
			capsule.Text = null;
			return capsule;
		}

		private static Guid SecureGuid()
		{
			Span<byte> buffer = stackalloc byte[16];
			RandomNumberGenerator.Fill(buffer);
			return new Guid(buffer);
		}

		private static Guid ComputeHash(string password)
		{
			using var sha384 = SHA384.Create();
			Span<byte> buffer = stackalloc byte[Encoding.UTF8.GetByteCount(password)];
			Encoding.UTF8.GetBytes(password, buffer);
			Span<byte> hash = stackalloc byte[sha384.HashSize >> 3];
			sha384.TryComputeHash(buffer, hash, out _);
			return new Guid(hash.Slice(0, 16));
		}

		private static bool SecureEquals(Guid g1, Guid g2)
		{
			Span<byte> span = stackalloc byte[32];
			g1.TryWriteBytes(span);
			g2.TryWriteBytes(span.Slice(16));

			var res = 0;
			for(int i = 0; i < span.Length >> 1; i++)
				res |= span[i] ^ span[i + 16];
			return res == 0;
		}

		private readonly DatabaseContext dbCtx;
	}
}
