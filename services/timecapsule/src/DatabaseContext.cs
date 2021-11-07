using System;
using System.Linq;
using System.Threading;
using Microsoft.EntityFrameworkCore;

namespace timecapsule
{
	public class UserContainer : Container { }
	public class TextContainer : Container { }

	public class DatabaseContext : DbContext
	{
		public DbSet<UserContainer> Users { get; set; }
		public DbSet<TextContainer> Texts { get; set; }

		private static readonly Thread CleanUpThread = new(_ =>
		{
			while(true)
			{
				Thread.Sleep(TimeSpan.FromMinutes(1));
				try
				{
					using var ctx = new DatabaseContext();
					var expire = DateTime.UtcNow.AddHours(-1);
					ctx.RemoveRange(ctx.Texts.Where(text => text.CreateDate < expire));
					ctx.RemoveRange(ctx.Users.Where(user => user.CreateDate < expire));
					ctx.SaveChanges();
				}
				catch { /* ignored */ }
			}
		}) { IsBackground = true, Priority = ThreadPriority.BelowNormal };

		protected override void OnConfiguring(DbContextOptionsBuilder builder)
		{
			builder.UseSqlite("filename=data.db");
		}

		protected override void OnModelCreating(ModelBuilder builder)
		{
			builder.Entity<TextContainer>()
				.Ignore(item => item.Text);

			builder.Entity<TextContainer>()
				.HasIndex(item => item.Author)
				.IsUnique(false);

			builder.Entity<TextContainer>()
				.HasIndex(item => item.CreateDate)
				.IsUnique(false);

			builder.Entity<UserContainer>()
				.Ignore(item => item.Id)
				.Ignore(item => item.Text)
				.Ignore(item => item.TimeCapsule)
				.HasKey(item => item.Author);

			builder.Entity<UserContainer>()
				.HasIndex(item => item.CreateDate)
				.IsUnique(false);
		}

		public static void Init()
		{
			using var ctx = new DatabaseContext();
			var created = ctx.Database.EnsureCreated();

			CleanUpThread.Start();

			if(!created)
				return;

			using var connection = ctx.Database.GetDbConnection();
			connection.Open();

			using var command = connection.CreateCommand();
			command.CommandText = "PRAGMA journal_mode=WAL;PRAGMA auto_vacuum=INCREMENTAL;PRAGMA synchronous=NORMAL;";
			command.ExecuteNonQuery();
		}

		public static void Flush()
		{
			using var ctx = new DatabaseContext();

			using var connection = ctx.Database.GetDbConnection();
			connection.Open();

			using var command = connection.CreateCommand();
			command.CommandText = "PRAGMA wal_checkpoint(FULL);";
			command.ExecuteNonQuery();
		}
	}
}
