using AutoMapper;
using mp.Entities;
using mp.Models.Users;

namespace mp
{
    public class AutoMapperProfile : Profile
    {
        public AutoMapperProfile()
        {
            CreateMap<RegisterModel, User>();
        }
    }
}
