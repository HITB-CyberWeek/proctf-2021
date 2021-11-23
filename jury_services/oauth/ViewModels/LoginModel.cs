using System.ComponentModel.DataAnnotations;

namespace OAuthServer.ViewModels
{
    public class LoginModel
    {
        [Required]
        public string Username { get; set; }

        [Required]
        public string Token { get; set; }

        public string ReturnUrl { get; set; }
    }
}