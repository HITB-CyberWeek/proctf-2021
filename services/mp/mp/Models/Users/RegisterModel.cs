using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

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
