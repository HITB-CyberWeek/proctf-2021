using System;
using System.Text.Json.Serialization;

namespace checker
{
	internal class PutResult
	{
		[JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }

		[JsonPropertyName("login")] public string Login { get; set; }
		[JsonPropertyName("pass")] public string Password { get; set; }
		[JsonPropertyName("id")] public Guid CapsuleId { get; set; }
		[JsonPropertyName("secret")] public Guid Secret { get; set; }
		[JsonPropertyName("capsule")] public string TimeCapsule { get; set; }
		[JsonPropertyName("cookie")] public string Cookie { get; set; }
	}
}
