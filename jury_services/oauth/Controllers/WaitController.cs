using Microsoft.AspNetCore.Mvc;
using OAuthServer.ViewModels;

namespace OAuthServer.Controllers
{
    [Route("/wait/")]
    public class WaitController : Controller
    {
        [HttpGet]
        public IActionResult Index([FromQuery(Name = "redirect_uri")] string redirectUri, int left = 60)
        {
            var model = new WaitModel {Max = left, ReturnUri = redirectUri};
            return View(model);
        }
    }
}