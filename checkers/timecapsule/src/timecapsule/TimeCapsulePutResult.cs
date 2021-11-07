using System;
using System.Text.Json.Serialization;

namespace checker.timecapsule
{
	internal class TimeCapsulePutResult : PutResult
	{
		[JsonPropertyName("login")] public string Login { get; set; }
		[JsonPropertyName("pass")] public string Password { get; set; }
		[JsonPropertyName("id")] public Guid CapsuleId { get; set; }
		[JsonPropertyName("secret")] public Guid Secret { get; set; }
		[JsonPropertyName("capsule")] public string TimeCapsule { get; set; }
		[JsonPropertyName("cookie")] public string Cookie { get; set; }
	}
}
