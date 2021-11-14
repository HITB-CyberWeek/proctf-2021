using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace mp.Models.Users
{
    public class RegisterModel : AuthenticateModel
    {
        [Required]
        [DefaultValue("John")]
        public string FirstName { get; set; }

        [Required]
        [DefaultValue("Doe")]
        public string LastName { get; set; }
    }
}
