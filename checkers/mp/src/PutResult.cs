using System.Text.Json.Serialization;

namespace checker
{
    internal class PutResult
    {
        [JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }

        [JsonPropertyName("login1")] public string Login1 { get; set; }
        [JsonPropertyName("pass1")] public string Password1 { get; set; }
        [JsonPropertyName("cookie1")] public string Cookie1 { get; set; }
        [JsonPropertyName("login2")] public string Login2 { get; set; }
        [JsonPropertyName("pass2")] public string Password2 { get; set; }
        [JsonPropertyName("cookie2")] public string Cookie2 { get; set; }

        [JsonPropertyName("productId")] public string ProductId { get; set; }
        [JsonPropertyName("orderId")] public string OrderId { get; set; }
        
    }
}