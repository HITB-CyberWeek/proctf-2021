using System;
using System.Collections.Generic;
using System.IdentityModel.Tokens.Jwt;
using System.Linq;
using System.Security.Claims;
using System.Text;
using System.Threading.Tasks;
using AutoMapper;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
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
        private IUserService userService;
        private IMapper mapper;
        private readonly AppSettings _appSettings;

        public UsersController(
            IUserService userService,
            IMapper mapper,
            IOptions<AppSettings> appSettings)
        {
            this.userService = userService;
            this.mapper = mapper;
            _appSettings = appSettings.Value;
        }

        [AllowAnonymous]
        [HttpPost("authenticateCookie")]
        public IActionResult AuthenticateCookie([FromBody] AuthenticateModel model)
        {
            var user = userService.ValidateCredentials(model.Login, model.Password);
            if (user == null)
                return BadRequest(new { message = "Username or password is incorrect" });

            var claimsIdentity = new ClaimsIdentity(CookieAuthenticationDefaults.AuthenticationScheme, ClaimTypes.Name, ClaimTypes.Role);
            claimsIdentity.AddClaims(new[]
            {
                new Claim(ClaimTypes.NameIdentifier, user.Login),
                // new Claim(ClaimTypes.Name, user.FirstName),
                // new Claim(ClaimTypes.Surname, user.LastName)
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
        [HttpPost("authenticateJwt")]
        public IActionResult AuthenticateJwt([FromBody] AuthenticateModel model)
        {
            var user = userService.ValidateCredentials(model.Login, model.Password);

            if (user == null)
                return BadRequest(new { message = "Username or password is incorrect" });

            var tokenHandler = new JwtSecurityTokenHandler();
            var key = Encoding.ASCII.GetBytes(_appSettings.RestApiJWTSecret);
            var tokenDescriptor = new SecurityTokenDescriptor
            {
                Subject = new ClaimsIdentity(new Claim[]
                {
                    new Claim(ClaimTypes.Name, user.Login)
                }),
                Expires = DateTime.UtcNow.AddDays(7),
                SigningCredentials = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature)
            };
            var token = tokenHandler.CreateToken(tokenDescriptor);
            var tokenString = tokenHandler.WriteToken(token);

            return Ok(new
            {
                //TODO return model here
                Login = user.Login,
                FirstName = user.FirstName,
                LastName = user.LastName,
                Token = tokenString
            });
        }

        [AllowAnonymous]
        [HttpPost("register")]
        public IActionResult Register([FromBody] RegisterModel model)
        {
            var user = mapper.Map<User>(model);

            try
            {
                userService.Create(user, model.Password);
                return Ok();
            }
            catch (ApiException ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }
    } 
}
