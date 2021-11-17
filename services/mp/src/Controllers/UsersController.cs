using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using mp.Entities;
using mp.Models.Users;
using mp.Services;

namespace mp.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]")]
    public class UsersController : ControllerBase
    {
        private UserService userService;

        public UsersController(UserService userService)
        {
            this.userService = userService;
        }

        [AllowAnonymous]
        [HttpGet("whoami")]
        public IActionResult Whoami()
        {
            return Ok(HttpContext?.User.FindCurrentUserId());
        }

        [AllowAnonymous]
        [HttpPost("login")]
        public IActionResult Login([FromBody] UserModel model)
        {
            var user = userService.ValidateCredentials(model.Login, model.Password);
            if (user == null)
                return BadRequest(new { message = "login or password is incorrect" });

            var claimsIdentity = new ClaimsIdentity(CookieAuthenticationDefaults.AuthenticationScheme, ClaimTypes.Name, ClaimTypes.Role);
            claimsIdentity.AddClaims(new[]
            {
                new Claim(ClaimTypes.Name, user.Login)
            });

            HttpContext.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme,
                new ClaimsPrincipal(claimsIdentity),
                new AuthenticationProperties
                {
                    IsPersistent = true
                });
            return Ok();
        }

        [AllowAnonymous]
        [HttpPost("register")]
        public async Task<IActionResult> Register([FromBody] UserModel model)
        {
            try
            {
                await userService.Create(model.Login, model.Password);
                return Ok();
            }
            catch (ApiException ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }
    } 
}
